from fastapi import Depends, Request, status, Response, APIRouter, Form
from sqlalchemy import text
from starlette.responses import HTMLResponse
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

from db.mysql import get_db_yph
from similar_product.product_proc import find_similar_products

router_yph = APIRouter()

templates = Jinja2Templates(directory="templates")


@router_yph.get("/users", response_class=HTMLResponse)
async def get_user(request: Request, response: Response, db: Session = Depends(get_db_yph)):
    query = text(f"select * from system_users limit :start,:size")
    datas = db.execute(query, {"start": 0, "size": 15}).all()
    return templates.TemplateResponse("yph_user.html", {"request": request, "error": "", "data": datas})


@router_yph.get("/products-process", response_class=HTMLResponse)
async def process_products(request: Request, db: Session = Depends(get_db_yph)):
    query = text(f"SELECT * FROM products")
    datas = db.execute(query, {"start": 0, "size": 15}).all()
    # 加载停用词
    with open("stopwords.txt", "r", encoding="utf-8") as f:
        stopwords = set(f.read().splitlines())

    return templates.TemplateResponse("yph_user.html", {"request": request, "error": "", "data": datas})


@router_yph.get("/find_similar", response_class=HTMLResponse)
async def find_similar(request: Request):
    return templates.TemplateResponse("similar_goods.html", {"request": request, "error": "", "data": []})


@router_yph.post("/find_similar", response_class=HTMLResponse)
async def find_similar(request: Request, goods_id: str = Form(...), top_n: int = Form(...),
                       db: Session = Depends(get_db_yph)):
    datas = find_similar_products(goods_id, top_n)
    datas_org = db.execute(text(f"SELECT `goods_id`,`supplier_code`,`goods_name`,`goods_desc`,`brand_name`,`goods_spec`,`goods_original_price`,`goods_original_naked_price`,`goods_pact_price`,`goods_pact_naked_price` FROM `shop_goods` AS `a` INNER JOIN `shop_goods_detail` AS `b` ON `a`.`goods_id`=`b`.`id` INNER JOIN `shop_goods_price` AS `c` ON `c`.`goods_code`=`b`.`goods_code` WHERE `a`.`tenant_id`=1 AND `a`.`goods_id`= :goods_id"), {"goods_id": goods_id})
    return templates.TemplateResponse("similar_goods.html", {"request": request, "error": "", "datas": datas, "datas_org": datas_org})
