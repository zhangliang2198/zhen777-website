from sklearn.feature_extraction.text import TfidfVectorizer
import jieba
from sqlalchemy import text
import numpy as np
import json
from db.mysql import get_db_yph
from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity


class DataHolder(object):
    td_vec_info = []
    word_vec_info = []
    meta_list_id = []
    meta_list_supplier = []
    meta_list_values = []
    similarity_matrix_td = []
    similarity_matrix_word = []


with open("./files/stopwords.txt", "r", encoding="utf-8") as f:
    stopwords = set(f.read().splitlines())
print(stopwords)


def tokenize_and_remove_stopwords(text):
    tokens = jieba.cut(text)
    return [t for t in tokens if t not in stopwords and not t.isspace()]


def process_product(curr: int = 0, size: int = 10000):
    # 分词和停用词移除
    db = next(get_db_yph())
    query = text(
        f"SELECT goods_id,supplier_code,goods_name,goods_desc,brand_name,goods_spec from shop_goods as a INNER JOIN shop_goods_detail as b on a.goods_id = b.id where a.tenant_id = 1 limit :start,:size")
    data = db.execute(query, {"start": curr, "size": size}).all()
    print("开始初始化数据")
    DataHolder.meta_list_id = [item.goods_id for item in data]
    DataHolder.meta_list_supplier = [item.supplier_code for item in data]
    DataHolder.meta_list_values = [
        tokenize_and_remove_stopwords(item.goods_name + item.goods_desc + item.brand_name + item.goods_spec) for item in
        data]
    print("分词完成")
    # 得到稀疏矩阵
    # 1. 保存词带词向量
    # vectorizer = TfidfVectorizer(tokenizer=lambda x: x, lowercase=False)
    # DataHolder.td_vec_info = vectorizer.fit_transform(item for item in DataHolder.meta_list_values)
    print("保存Tfidf词带词向量完成")
    # 得到相似度矩阵
    # DataHolder.similarity_matrix_td = cosine_similarity(DataHolder.td_vec_info)
    print("得到Tfidf相似度矩阵完成")
    # 训练Word2Vec模型
    sentences = [x for x in DataHolder.meta_list_values]
    model = Word2Vec(sentences, vector_size=100, window=3, min_count=1, workers=16)
    print("训练Word2Vec模型完成")
    # 计算词向量,并保存
    for item in DataHolder.meta_list_values:
        vectors = [model.wv[token] for token in item if token in model.wv.key_to_index]
        if not vectors:
            DataHolder.word_vec_info.append(np.zeros(model.vector_size))
        DataHolder.word_vec_info.append(np.mean(vectors, axis=0))
    print("计算词向量,并保存")
    # 得到相似度矩阵
    DataHolder.similarity_matrix_word = cosine_similarity(np.array([item for item in DataHolder.word_vec_info]))
    print("得到word2vec相似度矩阵")
    # 向量数据写入数据库，供之后查询相似
    # for index in range(0, len(meta_list_keys)):
    #     db_data = GoodsVec(goodsId=meta_list_keys[index], word2vec=0, word2vec_vec=json.dumps(Y[index].tolist()),
    #                        tdifd=json.dumps(meta_list_values[index]),
    #                        tdifd_vec=json.dumps(X[index].toarray().tolist()), supplier=meta_supplier_keys[index])
    #     db.add(db_data)
    #     db.commit()
    #     db.refresh(db_data)


def find_similar_products(query_id, top_n=5):
    # 找到商品所在的位置
    index = -1
    for i, item in enumerate(DataHolder.meta_list_id):
        if str(item) == str(query_id):
            index = i
            break

    if index == -1:
        return []

    sim_scores = list(enumerate(DataHolder.similarity_matrix_word[index]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    print(sim_scores)
    most_similar_products = tuple([DataHolder.meta_list_id[i] for i, _ in sim_scores[1:top_n + 1]])
    db = next(get_db_yph())
    query = text(
        f"SELECT `goods_id`,`supplier_code`,`goods_name`,`goods_desc`,`brand_name`,`goods_spec`,`goods_original_price`,`goods_original_naked_price`,`goods_pact_price`,`goods_pact_naked_price` FROM `shop_goods` AS `a` INNER JOIN `shop_goods_detail` AS `b` ON `a`.`goods_id`=`b`.`id` INNER JOIN `shop_goods_price` AS `c` ON `c`.`goods_code`=`b`.`goods_code` WHERE `a`.`tenant_id`=1 AND a.goods_id IN {most_similar_products}")
    datas = db.execute(query)
    return datas
