from functools import reduce

from sklearn.feature_extraction.text import TfidfVectorizer
import jieba
from sqlalchemy import text
import numpy as np
import json
from db.mysql import get_db_yph
from gensim.models import Word2Vec, KeyedVectors
from sklearn.metrics.pairwise import cosine_similarity
from concurrent.futures import ThreadPoolExecutor

from db.redis import redis_client


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


# 加载Word2vec模型
# wv_model = KeyedVectors.load_word2vec_format('./files/tencent-ailab-embedding-zh-d200-v0.2.0-s.txt', binary=True)


def tokenize_and_remove_stopwords(text):
    tokens = jieba.cut(text)
    return [t for t in tokens if t not in stopwords and not t.isspace()]


def process_product(curr: int = 0, size: int = 600000):
    # redis_client.flushdb()
    # 分词和停用词移除
    db = next(get_db_yph())
    query = text(
        f"SELECT goods_id,supplier_code,goods_name,goods_desc,brand_name,goods_spec from shop_goods as a INNER JOIN shop_goods_detail as b on a.goods_id = b.id where a.tenant_id = 1 limit :start,:size")
    data = db.execute(query, {"start": curr, "size": size}).all()
    print("开始初始化数据")
    DataHolder.meta_list_id = [item.goods_id for item in data]
    DataHolder.meta_list_supplier = [item.supplier_code for item in data]
    DataHolder.meta_list_values = [
        tokenize_and_remove_stopwords(str(item.goods_name) + str(item.goods_desc) + str(item.brand_name) + str(item.goods_spec)) for item in
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
    model = Word2Vec(sentences, vector_size=100, window=2, min_count=1, workers=16)
    print("训练Word2Vec模型完成")
    # 计算词向量,并保存
    for item in DataHolder.meta_list_values:
        vectors = [model.wv[token] for token in item if token in model.wv.key_to_index]
        if not vectors:
            DataHolder.word_vec_info.append(np.zeros(model.vector_size))
        DataHolder.word_vec_info.append(np.mean(vectors, axis=0))
    print("计算词向量,并保存")
    # 得到相似度矩阵
    DataHolder.similarity_matrix_word = find_top_k_similar_items(DataHolder.word_vec_info, 20)
    print("得到word2vec相似度矩阵")

    # 向量数据写入数据库，供之后查询相似
    # for index in range(0, len(meta_list_keys)):
    #     db_data = GoodsVec(goodsId=meta_list_keys[index], word2vec=0, word2vec_vec=json.dumps(Y[index].tolist()),
    #                        tdifd=json.dumps(meta_list_values[index]),
    #                        tdifd_vec=json.dumps(X[index].toarray().tolist()), supplier=meta_supplier_keys[index])
    #     db.add(db_data)
    #     db.commit()
    #     db.refresh(db_data)


# 将向量数据分成批次
def batch(iterable, batch_size):
    for i in range(0, len(iterable), batch_size):
        yield iterable[i:i + batch_size]


# 计算所有商品与所有商品的余弦相似度，并返回前k个最相似商品的索引
def find_top_k_similar_items(vectors, k, batch_size=1):
    top_k_indices_list = []
    index = 0
    for vector_group in batch(vectors, batch_size):
        batch_similarities = cosine_similarity(vector_group, vectors)
        # 找到前k个最相似商品的索引
        top_k_batch_indices = np.argpartition(batch_similarities, -k)[:, -k:]
        # 直接往redis中存储，不保存，注意这里是索引需要转换成ID
        ids = [DataHolder.meta_list_id[pos] for pos in top_k_batch_indices.tolist()[0]]
        redis_client.set(f"product:{DataHolder.meta_list_id[index]}:similar", json.dumps(ids))
        # top_k_indices_list.extend(top_k_batch_indices)
        index += 1
        del batch_similarities
        del top_k_batch_indices
        del ids

    return np.array(top_k_indices_list)


def find_similar_products(query_id, top_n=5):
    # sim_scores = list(enumerate(DataHolder.similarity_matrix_word[index]))
    sim_scores = json.loads(redis_client.get(f"product:{query_id}:similar"))
    # sim_scores = sorted(sim_scores, key=lambda x: x[0], reverse=True)
    # most_similar_products = tuple([DataHolder.meta_list_id[k] for i, k in sim_scores[1:top_n + 1]])

    db = next(get_db_yph())
    # 翻转列表
    id_list = list(sim_scores[0:top_n])[::-1]
    print(id_list)

    # 改成元组，查询用
    most_similar_products = tuple(id_list)

    # 拼接查询参数
    id_str = reduce(lambda x, y: str(x) + "," + str(y), id_list)
    query = text(
        f"SELECT `goods_id`,`supplier_code`,`goods_name`,`goods_desc`,`brand_name`,`goods_spec`,`goods_original_price`,`goods_original_naked_price`,`goods_pact_price`,`goods_pact_naked_price` FROM `shop_goods` AS `a` INNER JOIN `shop_goods_detail` AS `b` ON `a`.`goods_id`=`b`.`id` INNER JOIN `shop_goods_price` AS `c` ON `c`.`goods_code`=`b`.`goods_code` WHERE `a`.`tenant_id`=1 AND a.goods_id IN {most_similar_products} order by field(a.goods_id,{id_str})")
    datas = db.execute(query)
    return datas
