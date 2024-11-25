from neo4j_util import *


def main():

    ##配置指向Neo4j数据库的URI、用户名和密码
    neo4j_uri = "neo4j://localhost:7687"
    neo4j_username = "neo4j"
    neo4j_password = "12345678"
    neo4j_database = "neo4j"

    #待导入Neo4j的目录
    import_root_folder = "E:/software/ai/neo4j-community-5.25.1/import"

    driver = connect_neo4j(neo4j_uri=neo4j_uri, neo4j_username=neo4j_username, neo4j_password=neo4j_password)

    #在neo4j中创建contraint
    create_constraint_in_neo4j(driver)
    #导入create_final_documents.parquet文件到neo4j
    import_create_final_documents_file(import_root_folder,neo4j_database,driver)
    #导入create_final_text_units.parquet文件到neo4j
    import_create_final_text_units_file(import_root_folder,neo4j_database,driver)
    #导入create_final_entities.parquet文件到neo4j
    import_create_final_entities_file(import_root_folder,neo4j_database,driver)
    #导入create_final_relationships.parquet文件到neo4j
    import_create_final_relationships_file(import_root_folder,neo4j_database,driver)
    #导入create_final_reports.parquet文件到neo4j
    import_create_final_community_reports_file(import_root_folder,neo4j_database,driver)
    #导入create_final_communities.parquet文件到neo4j
    import_create_final_communities_file(import_root_folder,neo4j_database,driver)


if __name__ == '__main__':
     main()