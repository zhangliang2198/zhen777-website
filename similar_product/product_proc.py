import threading
from functools import reduce
from heapq import nlargest

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
    model: Word2Vec
    vectorizer: TfidfVectorizer


# 将停用词组成一个set
with open("./files/stopwords.txt", "r", encoding="utf-8") as f:
    stopwords = set(f.read().splitlines())


# 加载Word2vec模型
# wv_model = KeyedVectors.load_word2vec_format('./files/tencent-ailab-embedding-zh-d200-v0.2.0-s.txt', binary=True)


# 切词，返回切词后的列表
def tokenize_and_remove_stopwords(sentence):
    tokens = jieba.cut(sentence)
    return [t for t in tokens if t not in stopwords and not t.isspace()]


def process_product(curr: int = 0, size: int = 10000):
    # redis_client.flushdb()
    # 分词和停用词移除
    db = next(get_db_yph())
    query = text(
        f"SELECT goods_id,supplier_code,goods_name,goods_desc,brand_name,goods_spec from shop_goods as a INNER JOIN shop_goods_detail as b on a.goods_id = b.id where a.tenant_id = 1 and a.is_enable=1 limit :start,:size")
    data = db.execute(query, {"start": curr, "size": size}).all()
    print("开始初始化数据")
    DataHolder.meta_list_id = [item.goods_id for item in data]
    DataHolder.meta_list_supplier = [item.supplier_code for item in data]

    # # 使用多线程进行分词
    # batch_size = len(vectors) // num_threads
    # threads = []
    # for i in range(num_threads):
    #     start = i * chunk_size
    #     # 最后一部分用,使用 vectors.shape 的长度  即：vectors.shape[0]
    #     end = (i + 1) * chunk_size if i < num_threads - 1 else vectors.shape[0]
    #     thread = threading.Thread(target=find_top_k_similar_items, args=(vectors, k, start, end, 5))
    #     threads.append(thread)
    #     thread.start()

    DataHolder.meta_list_values = [
        tokenize_and_remove_stopwords(
            str(item.goods_name) + str(item.goods_desc) + str(item.brand_name) + str(item.goods_spec)) for item in
        data]
    print("分词完成")
    # 得到稀疏矩阵
    # 1. 保存词带词向量
    DataHolder.vectorizer = TfidfVectorizer(tokenizer=lambda x: x, lowercase=False)
    DataHolder.td_vec_info = DataHolder.vectorizer.fit_transform(item for item in DataHolder.meta_list_values)
    print("保存Tfidf词带词向量完成")
    # 得到相似度矩阵
    # DataHolder.similarity_matrix_td = cosine_similarity(DataHolder.td_vec_info)
    print("得到Tfidf相似度矩阵完成")
    # 训练Word2Vec模型
    # 每个sentence这里是一个列表["fwewef,"123123"]
    # sentences = [x for x in DataHolder.meta_list_values]
    # DataHolder.model = Word2Vec(sentences, vector_size=100, window=2, min_count=1, workers=32)
    # print("训练Word2Vec模型完成")
    # # 计算词向量,并保存
    # for item in DataHolder.meta_list_values:
    #     # 针对每项 分过词的列表，一个token是一个单词，拿到这个token的 词向量数据，词向量数据是一个 【token数量 * 100】 的二维数组，
    #     vectors = [DataHolder.model.wv[token] for token in item if token in DataHolder.model.wv.key_to_index]
    #     if not vectors:
    #         # 如果找不到这个100维的向量值，则用100维度的 0 替代
    #         DataHolder.word_vec_info.append(np.zeros(DataHolder.model.vector_size))
    #     # 如果找的到 则在 word_vec_info 对应的索引添加 【token数量 * 100】维度向量的每一列的平均值，得到一个100个数据的一维数组，表示当前sentence的向量值
    #     else:
    #         DataHolder.word_vec_info.append(np.mean(vectors, axis=0))
    print("计算词向量,并保存")
    # 得到相似度矩阵，只取前20个相似商品，这里是不是可以进行多线程的优化
    # DataHolder.similarity_matrix_word = find_top_k_similar_items(DataHolder.word_vec_info, 20)
    # mult_find(np.array(DataHolder.word_vec_info), 20, 5, 32)
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
# 通过生成器，每次取 batch_size个数据出来
def batch(iterable, batch_size):
    for i in range(0, len(iterable), batch_size):
        yield iterable[i:i + batch_size]


# 异步计算，不影响主程序执行
def mult_find(vectors, k, batch_size=5, num_threads=32):
    chunk_size = len(vectors) // num_threads
    threads = []
    for i in range(num_threads):
        start = i * chunk_size
        # 最后一部分用,使用 vectors.shape 的长度  即：vectors.shape[0]
        end = (i + 1) * chunk_size if i < num_threads - 1 else vectors.shape[0]
        thread = threading.Thread(target=find_top_k_similar_items, args=(vectors, k, start, end, 5))
        threads.append(thread)
        thread.start()


# 计算所有商品与所有商品的余弦相似度，并返回前k个最相似商品的索引
def find_top_k_similar_items(vectors, k, start, end, batch_size=5):
    # vectors 是一个包含所有 sentence 向量值【100个数】的 列表
    # for vector_group in batch(vectors, batch_size):
    for index in range(start, end):
        print(vectors[index])
        # 使用reshape(1, -1)，转换为一行的矩阵，flatten()使用flatten又转为数组
        batch_similarities = cosine_similarity(vectors[index].reshape(1, -1), vectors).flatten()

        # 找到前k个最相似商品的索引.argpartition 默认按最后一个真正的余弦相似度【这里其实有3个维度了】，也就是真实的相似度
        top_k_batch_indices = np.argpartition(batch_similarities, -k)[-k:]
        # 直接往redis中存储，不保存，注意这里是索引需要转换成ID

        # top_k_batch_indices.tolist()[0]。表示位置，因为用 np.argpartition 进行了排序
        ids = [DataHolder.meta_list_id[pos] for pos in top_k_batch_indices.tolist()]
        redis_client.set(f"product:{DataHolder.meta_list_id[index]}:similar", json.dumps(ids))

        del top_k_batch_indices
        del batch_similarities
        del ids

    # return np.array(top_k_indices_list)


def find_similar_products(query_id, top_n=5):
    db = next(get_db_yph())
    datas_org = db.execute(text(
        f"SELECT `goods_id`,`supplier_code`,`goods_name`,`goods_desc`,`brand_name`,`goods_spec`,`goods_original_price`,`goods_original_naked_price`,`goods_pact_price`,`goods_pact_naked_price` FROM `shop_goods` AS `a` INNER JOIN `shop_goods_detail` AS `b` ON `a`.`goods_id`=`b`.`id` LEFT JOIN `shop_goods_price` AS `c` ON `c`.`goods_code`=`b`.`goods_code` WHERE `a`.`tenant_id`=1 AND `a`.`goods_id`= :goods_id"),
        {"goods_id": query_id})

    if not datas_org:
        return []
    org_token = [tokenize_and_remove_stopwords(
        str(item.goods_name) + str(item.goods_desc) + str(item.brand_name) + str(item.goods_spec))
        for item in datas_org][0]

    query_vector = DataHolder.vectorizer.transform([org_token])
    similarities = cosine_similarity(query_vector, DataHolder.td_vec_info)
    top_similar_products = nlargest(top_n, enumerate(similarities[0]), key=lambda x: x[1])
    # vectors = [DataHolder.model.wv[token] for token in org_token if token in DataHolder.model.wv.key_to_index]

    # if not vectors:
    #     # 如果找不到这个100维的向量值，则用100维度的 0 替代
    #     c_mean = np.zeros(DataHolder.model.vector_size)
    # # 如果找的到 则在 word_vec_info 对应的索引添加 【token数量 * 100】维度向量的每一列的平均值，得到一个100个数据的一维数组，表示当前sentence的向量值
    # else:
    #     c_mean = np.mean(vectors, axis=0)
    index = [product_index for product_index, similarity in top_similar_products]
    ids = [DataHolder.meta_list_id[pos] for pos in index]
    # org_vec = cosine_similarity(c_mean.reshape(1, -1), DataHolder.word_vec_info).flatten()
    # 找到前k个最相似商品的索引.argpartition 默认按最后一个真正的余弦相似度【这里其实有3个维度了】，也就是真实的相似度
    # 直接往redis中存储，不保存，注意这里是索引需要转换成ID

    # top_k_batch_indices.tolist()[0]。表示位置，因为用 np.argpartition 进行了排序


    # sim_scores = list(enumerate(DataHolder.similarity_matrix_word[index]))
    # sim_scores = json.loads(redis_client.get(f"product:{query_id}:similar"))
    # sim_scores = sorted(sim_scores, key=lambda x: x[0], reverse=True)
    # most_similar_products = tuple([DataHolder.meta_list_id[k] for i, k in sim_scores[1:top_n + 1]])

    # 翻转列表
    id_list = list(ids)

    # 改成元组，查询用
    most_similar_products = tuple(id_list)

    # 拼接查询参数
    id_str = reduce(lambda x, y: str(x) + "," + str(y), id_list)
    query = text(
        f"SELECT `goods_id`,`supplier_code`,`goods_name`,`goods_desc`,`brand_name`,`goods_spec`,`goods_original_price`,`goods_original_naked_price`,`goods_pact_price`,`goods_pact_naked_price` FROM `shop_goods` AS `a` INNER JOIN `shop_goods_detail` AS `b` ON `a`.`goods_id`=`b`.`id` INNER JOIN `shop_goods_price` AS `c` ON `c`.`goods_code`=`b`.`goods_code` WHERE `a`.`tenant_id`=1 AND a.goods_id IN {most_similar_products} order by field(a.goods_id,{id_str})")
    datas = db.execute(query)

    return datas
