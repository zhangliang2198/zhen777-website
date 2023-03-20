from functools import reduce

from sklearn.feature_extraction.text import TfidfVectorizer
import jieba
from sqlalchemy import text
import numpy as np
import json

from db import redis
from db.mysql import get_db_yph
from gensim.models import Word2Vec, KeyedVectors
from sklearn.metrics.pairwise import cosine_similarity
from concurrent.futures import ThreadPoolExecutor

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
wv_model = KeyedVectors.load_word2vec_format('./files/tencent_word2vec_l.txt', binary=True)

# 分词函数
def cut_words(text):
    words = jieba.cut(text)
    words = [word.strip() for word in words if word.strip() and word not in stopwords]
    return words


# 计算tfidf函数
def calculate_tfidf(corpus):
    vectorizer = TfidfVectorizer(tokenizer=cut_words)
    tfidf = vectorizer.fit_transform(corpus)
    return vectorizer, tfidf


# 计算向量函数
def calculate_vectors(text, vectorizer):
    words = cut_words(text)
    weights = vectorizer.transform([text]).toarray().squeeze()
    vectors = []
    for word, weight in zip(words, weights):
        try:
            vector = wv_model.get_vector(word)
            vectors.append(vector * weight)
        except KeyError:
            pass
    return np.array(vectors).mean(axis=0)


# 计算余弦相似度函数
def cosine_similarity(u, v):
    return np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v))


# 相似商品查询函数
def find_similar_products(query, products):
    # 计算tfidf
    corpus = [product['desc'] for product in products]
    vectorizer, tfidf = calculate_tfidf(corpus)

    # 计算商品向量
    for product in products:
        product['vector'] = calculate_vectors(product['desc'], vectorizer)

    # 查询商品向量
    query_vector = calculate_vectors(query, vectorizer)

    # 计算相似度
    similarities = []
    for product in products:
        similarity = cosine_similarity(query_vector, product['vector'])
        similarities.append((product['id'], similarity))

    # 按相似度从高到低排序
    similarities.sort(key=lambda x: x[1], reverse=True)

    # 返回相似商品列表
    similar_products = [{'id': product_id, 'similarity': similarity} for product_id, similarity in similarities]
    return similar_products
def save_similar_products(product_id, similar_products, r, k):
    # 分词和停用词移除
    db = next(get_db_yph())
    query = text(
        f"SELECT goods_id,supplier_code,goods_name,goods_desc,brand_name,goods_spec from shop_goods as a INNER JOIN shop_goods_detail as b on a.goods_id = b.id where a.tenant_id = 1 limit :start,:size")
    products = db.execute(query, {"start": 0, "size": 10000}).all()
    print("开始初始化数据")
    DataHolder.meta_list_id = [item.goods_id for item in products]
    DataHolder.meta_list_supplier = [item.supplier_code for item in products]
    DataHolder.meta_list_brand = [item.brand_name for item in products]
    # 只保留相似度最高的k个商品
    similar_products = sorted(similar_products, key=lambda x: x[1], reverse=True)[:k]
    # 将相似商品id和相似度存储到Redis中
    key = f"similar_products:{product_id}"
    for i, (id, similarity) in enumerate(similar_products):
        r.hset(key, id, similarity)

        corpus = [product['desc'] for product in products]
        vectorizer, tfidf = calculate_tfidf(corpus)
        for product in products:
            product_id = product['id']
        vector = calculate_vectors(product['desc'], vectorizer)
        similarities = []
        for other_product in products:
            if other_product['id'] != product_id:
                other_vector = other_product['vector']
        similarity = cosine_similarity(vector, other_vector)
        similarities.append((other_product['id'], similarity))
        save_similar_products(product_id, similarities, r, k=5)
