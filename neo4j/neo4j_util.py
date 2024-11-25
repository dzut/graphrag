import pandas as pd
from neo4j import GraphDatabase
import time

"""
 参考链接：https://zhuanlan.zhihu.com/p/710216509
"""


"""
 方法描述：连接neo4j
"""
def connect_neo4j0(neo4j_host, neo4j_port, neo4j_username=None, neo4j_password=None):
    try:
         uri = f'bolt://{neo4j_host}:{neo4j_port}'
         driver = GraphDatabase.driver(uri, auth=(neo4j_username, neo4j_password))
         return driver
    except Exception as e:
         print(e)
         return None

"""
 方法描述：连接neo4j
"""
def connect_neo4j(neo4j_uri, neo4j_username=None, neo4j_password=None):
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
        return driver
    except Exception as e:
        print(e)
        return None

"""
方法描述：用于批量执行制定的statement到neo4j
参数：statement:cypher语句
     df:为待导入的数据集
     batch_size:每次批量导入的行数
"""
def batched_import(statement, df, batch_size=1000,neo4j_database=None,driver=None):
    try:
        total = len(df)
        start_s = time.time()
        for start in range(0, total, batch_size):
            batch = df.iloc[start: min(start + batch_size, total)]
            result = driver.execute_query("UNWIND $rows AS value " + statement,
                                      rows=batch.to_dict('records'),
                                      database_=neo4j_database)
        print(f'{total} rows in {time.time() - start_s} s.')
        return total
    except Exception as e:
        print(e)
        return None

"""
 方法描述：在neo4j中创建constraint
"""
def create_constraint_in_neo4j(driver=None):
    print("进入方法：create_constraint_in_neo4j()")
    try:
        statements = """
        create constraint chunk_id if not exists for (c:__Chunk__) require c.id is unique;
        create constraint document_id if not exists for (d:__Document__) require d.id is unique;
        create constraint entity_id if not exists for (c:__Community__) require c.community is unique;
        create constraint entity_id if not exists for (e:__Entity__) require e.id is unique;
        create constraint entity_title if not exists for (e:__Entity__) require e.name is unique;
        create constraint entity_title if not exists for (e:__Covariate__) require e.title is unique;
        """.split(";")

        ##创建一组constraint
        for statement in statements:
            if len((statement or "").strip()) > 0:
                driver.execute_query(statement)
    except Exception as e:
        print(e)

"""
 方法描述：导入create_final_documents.parquet的内容到Neo4j
"""
def import_create_final_documents_file(graphrag_folder,neo4j_database,driver=None):
    print("进入方法：import_create_final_documents_file()")
    try:
        doc_df = pd.read_parquet(f'{graphrag_folder}/create_final_documents.parquet', columns=["id", "title"])
        doc_df.head(2)

        #导入文档
        statement = """
        MERGE (d:__Document__ {id:value.id})
        SET d += value {.title}
        """
        batched_import(statement=statement, df=doc_df,neo4j_database=neo4j_database,driver=driver)
    except Exception as e:
        print(e)

"""
 方法描述：导入create_final_text_units.parquet的内容到Neo4j
"""
def import_create_final_text_units_file(graphrag_folder,neo4j_database,driver=None):
    print("进入方法：import_create_final_text_units_file()")
    try:
        text_df = pd.read_parquet(f'{graphrag_folder}/create_final_text_units.parquet',columns=["id", "text", "n_tokens", "document_ids"])
        text_df.head(2)

        statement = """
        MERGE (c:__Chunk__ {id:value.id})
        SET c += value {.text, .n_tokens}
        WITH c, value
        UNWIND value.document_ids AS document
        MATCH (d:__Document__ {id:document})
        MERGE (c)-[:PART_OF]->(d)
        """
        batched_import(statement=statement,df=text_df,neo4j_database=neo4j_database,driver=driver)
    except Exception as e:
        print(e)

"""
 方法描述：导入create_final_entities.parquet的内容到Neo4j
"""
def import_create_final_entities_file(graphrag_folder,neo4j_database,driver=None):
    print("进入方法：import_create_final_entities_file()")
    try:
        entity_df = pd.read_parquet(f'{graphrag_folder}/create_final_entities.parquet',columns=["name", "type", "description", "human_readable_id", "id", "description_embedding","text_unit_ids"])
        entity_df.head(2)
        entity_statement = """
            MERGE (e:__Entity__ {id:value.id})
            SET e += value {.human_readable_id, .description, name:replace(value.name,'"','')}
            WITH e, value
            UNWIND value.text_unit_ids AS text_unit
            MATCH (c:__Chunk__ {id:text_unit})
            MERGE (c)-[:HAS_ENTITY]->(e)
        """
        batched_import(statement=entity_statement, df=entity_df,neo4j_database=neo4j_database,driver=driver)
    except Exception as e:
        print(e)

"""
 方法描述：导入create_final_relationships.parquet的内容到Neo4j
"""
def import_create_final_relationships_file(graphrag_folder,neo4j_database,driver=None):
    print("进入方法：import_create_final_relationships_file()")
    try:
        rel_df = pd.read_parquet(f'{graphrag_folder}/create_final_relationships.parquet',
                         columns=["source", "target", "id", "rank", "weight", "human_readable_id", "description","text_unit_ids"])
        rel_df.head(2)

        rel_statement = """
            MATCH (source:__Entity__ {name:replace(value.source,'"','')})
            MATCH (target:__Entity__ {name:replace(value.target,'"','')})
            // not necessary to merge on id as there is only one relationship per pair
            MERGE (source)-[rel:RELATED {id: value.id}]->(target)
            SET rel += value {.rank, .weight, .human_readable_id, .description, .text_unit_ids}
            RETURN count(*) as createdRels
        """
        batched_import(statement=rel_statement, df=rel_df,neo4j_database=neo4j_database,driver=driver)
    except Exception as e:
        print(e)

"""
 方法描述：导入create_final_communities.parquet的内容到Neo4j
"""
def import_create_final_communities_file(graphrag_folder,neo4j_database,driver=None):
    print("进入方法：import_create_final_communities_file()")
    try:
        community_df = pd.read_parquet(f'{graphrag_folder}/create_final_communities.parquet',
                               columns=["id", "level", "title", "text_unit_ids", "relationship_ids"])
        community_df.head(2)
        statement = """
        MERGE (c:__Community__ {community:value.id})
        SET c += value {.level, .title}
        /*
        UNWIND value.text_unit_ids as text_unit_id
        MATCH (t:__Chunk__ {id:text_unit_id})
        MERGE (c)-[:HAS_CHUNK]->(t)
        WITH distinct c, value
        */
        WITH *
        UNWIND value.relationship_ids as rel_id
        MATCH (start:__Entity__)-[:RELATED {id:rel_id}]->(end:__Entity__)
        MERGE (start)-[:IN_COMMUNITY]->(c)
        MERGE (end)-[:IN_COMMUNITY]->(c)
        RETURN count(distinct c) as createdCommunities
        """
        batched_import(statement=statement, df=community_df,neo4j_database=neo4j_database,driver=driver)
    except Exception as e:
        print(e)


"""
 方法描述：导入create_final_community_reports.parquet的内容到Neo4j
"""
def import_create_final_community_reports_file(graphrag_folder,neo4j_database,driver=None):
    print("进入方法：import_create_final_community_reports_file()")
    try:
        community_report_df = pd.read_parquet(f'{graphrag_folder}/create_final_community_reports.parquet',
                                      columns=["id", "community", "level", "title", "summary", "findings", "rank",
                                               "rank_explanation", "full_content"])
        community_report_df.head(2)

        # import communities
        community_statement = """MATCH (c:__Community__ {community: value.community})
        SET c += value {.level, .title, .rank, .rank_explanation, .full_content, .summary}
        WITH c, value
        UNWIND range(0, size(value.findings)-1) AS finding_idx
        WITH c, value, finding_idx, value.findings[finding_idx] as finding
        MERGE (c)-[:HAS_FINDING]->(f:Finding {id: finding_idx})
        SET f += finding"""
        batched_import(statement=community_statement, df=community_report_df,neo4j_database=neo4j_database,driver=driver)
    except Exception as e:
        print(e)