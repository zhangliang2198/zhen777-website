from sqlalchemy import Column, Integer, String, Boolean, DateTime, create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class GoodsVec(Base):
    __tablename__ = "goods_vec_info"

    id = Column(Integer, primary_key=True, index=True)
    goodsId = Column(String(64), index=True)
    word2vec = Column(String(2048))
    word2vec_vec = Column(String(2048))
    tdifd = Column(String(2048))
    tdifd_vec = Column(String(2048))
    supplier = Column(String(2048))
