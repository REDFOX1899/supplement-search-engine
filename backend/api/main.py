## 2. Backend - FastAPI Application

# backend/api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from elasticsearch import Elasticsearch
import uvicorn

app = FastAPI(
    title="SupplementSearch Pro API",
    description="NIH DSLD Supplement Search Engine",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Elasticsearch connection
es = Elasticsearch(
    cloud_id=os.getenv("ab6155d198004e968e21b6a527d0a426"),
    basic_auth=(os.getenv("elastic"), os.getenv("vV36DPgql3W0qBz5yLDt594r"))
)

# Pydantic models
class SearchQuery(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = {}
    page: Optional[int] = 1
    size: Optional[int] = 20

class Supplement(BaseModel):
    dsld_id: str
    product_name: str
    brand_name: Optional[str]
    supplement_form: str
    active_ingredients: List[Dict[str, Any]]
    market_status: str

@app.get("/")
async def root():
    return {"message": "SupplementSearch Pro API", "status": "healthy"}

@app.get("/health")
async def health_check():
    try:
        es.ping()
        return {"status": "healthy", "elasticsearch": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.post("/search")
async def search_supplements(search_query: SearchQuery):
    try:
        # Build Elasticsearch query
        query = {
            "bool": {
                "must": [],
                "filter": []
            }
        }
        
        # Main search query
        if search_query.query:
            query["bool"]["must"].append({
                "multi_match": {
                    "query": search_query.query,
                    "fields": [
                        "product_name^3",
                        "brand_name^2",
                        "active_ingredients.name^2",
                        "all_ingredients",
                        "health_benefits"
                    ],
                    "fuzziness": "AUTO"
                }
            })
        else:
            query["bool"]["must"].append({"match_all": {}})
        
        # Apply filters
        if search_query.filters:
            if "supplement_form" in search_query.filters:
                query["bool"]["filter"].append({
                    "term": {"supplement_form": search_query.filters["supplement_form"]}
                })
            
            if "brand_name" in search_query.filters:
                query["bool"]["filter"].append({
                    "term": {"brand_name.keyword": search_query.filters["brand_name"]}
                })
            
            if "price_range" in search_query.filters:
                price_range = search_query.filters["price_range"]
                query["bool"]["filter"].append({
                    "range": {
                        "price": {
                            "gte": price_range.get("min", 0),
                            "lte": price_range.get("max", 1000)
                        }
                    }
                })
        
        # Calculate pagination
        from_index = (search_query.page - 1) * search_query.size
        
        # Execute search
        response = es.search(
            index="supplements",
            body={
                "query": query,
                "from": from_index,
                "size": search_query.size,
                "highlight": {
                    "fields": {
                        "product_name": {},
                        "active_ingredients.name": {}
                    }
                },
                "aggs": {
                    "supplement_forms": {
                        "terms": {"field": "supplement_form", "size": 10}
                    },
                    "brands": {
                        "terms": {"field": "brand_name.keyword", "size": 20}
                    },
                    "ingredient_categories": {
                        "nested": {"path": "active_ingredients"},
                        "aggs": {
                            "categories": {
                                "terms": {"field": "active_ingredients.category", "size": 15}
                            }
                        }
                    }
                }
            }
        )
        
        # Format response
        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]
        aggregations = response["aggregations"]
        
        results = []
        for hit in hits:
            source = hit["_source"]
            highlight = hit.get("highlight", {})
            
            result = {
                "dsld_id": source["dsld_id"],
                "product_name": source["product_name"],
                "brand_name": source.get("brand_name", ""),
                "supplement_form": source["supplement_form"],
                "serving_size": source.get("serving_size", ""),
                "market_status": source["market_status"],
                "active_ingredients": source.get("active_ingredients", []),
                "suggested_use": source.get("suggested_use", ""),
                "url": source.get("url", ""),
                "highlight": highlight,
                "score": hit["_score"]
            }
            results.append(result)
        
        return {
            "results": results,
            "total": total,
            "page": search_query.page,
            "size": search_query.size,
            "aggregations": aggregations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/supplement/{dsld_id}")
async def get_supplement(dsld_id: str):
    try:
        response = es.get(index="supplements", id=dsld_id)
        return response["_source"]
    except Exception as e:
        raise HTTPException(status_code=404, detail="Supplement not found")

@app.get("/autocomplete")
async def autocomplete(q: str):
    try:
        response = es.search(
            index="supplements",
            body={
                "suggest": {
                    "product_suggest": {
                        "prefix": q,
                        "completion": {
                            "field": "product_name.suggest",
                            "size": 10
                        }
                    }
                }
            }
        )
        
        suggestions = []
        for suggestion in response["suggest"]["product_suggest"][0]["options"]:
            suggestions.append({
                "text": suggestion["text"],
                "score": suggestion["_score"]
            })
        
        return {"suggestions": suggestions}
    except Exception as e:
        return {"suggestions": []}

@app.get("/analytics/trends")
async def get_trends():
    try:
        response = es.search(
            index="supplements",
            body={
                "size": 0,
                "aggs": {
                    "top_ingredients": {
                        "nested": {"path": "active_ingredients"},
                        "aggs": {
                            "ingredient_names": {
                                "terms": {
                                    "field": "active_ingredients.name.keyword",
                                    "size": 20
                                }
                            }
                        }
                    },
                    "top_brands": {
                        "terms": {
                            "field": "brand_name.keyword",
                            "size": 15
                        }
                    },
                    "supplement_forms": {
                        "terms": {
                            "field": "supplement_form",
                            "size": 10
                        }
                    },
                    "market_status": {
                        "terms": {
                            "field": "market_status",
                            "size": 5
                        }
                    }
                }
            }
        )
        
        return response["aggregations"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
