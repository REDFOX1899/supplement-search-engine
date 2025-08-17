# 3. Data Processing Script

# backend/data_processing/data_importer.py
import pandas as pd
import json
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DSLDImporter:
    def __init__(self):
        self.es = Elasticsearch(
             cloud_id=os.getenv("ab6155d198004e968e21b6a527d0a426"),
             basic_auth=(os.getenv("elastic"), os.getenv("vV36DPgql3W0qBz5yLDt594r"))
        )
        
    def create_index_mapping(self):
        """Create the supplements index with proper mapping"""
        mapping = {
            "settings": {
                "number_of_shards": 2,
                "number_of_replicas": 1,
                "analysis": {
                    "analyzer": {
                        "supplement_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "stop", "synonym_filter"]
                        }
                    },
                    "filter": {
                        "synonym_filter": {
                            "type": "synonym",
                            "synonyms": [
                                "vitamin c,ascorbic acid",
                                "vitamin d,cholecalciferol",
                                "omega-3,fish oil",
                                "coq10,coenzyme q10"
                            ]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "dsld_id": {"type": "keyword"},
                    "url": {"type": "keyword", "index": False},
                    "product_name": {
                        "type": "text",
                        "analyzer": "supplement_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "suggest": {"type": "completion"}
                        }
                    },
                    "brand_name": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "bar_code": {"type": "keyword"},
                    "net_contents": {"type": "text"},
                    "serving_size": {"type": "text"},
                    "product_type": {"type": "keyword"},
                    "supplement_form": {"type": "keyword"},
                    "date_entered": {"type": "date", "format": "yyyy-MM-dd"},
                    "market_status": {"type": "keyword"},
                    "suggested_use": {"type": "text"},
                    "active_ingredients": {
                        "type": "nested",
                        "properties": {
                            "name": {
                                "type": "text",
                                "analyzer": "supplement_analyzer",
                                "fields": {"keyword": {"type": "keyword"}}
                            },
                            "category": {"type": "keyword"},
                            "amount": {"type": "float"},
                            "unit": {"type": "keyword"},
                            "daily_value_percent": {"type": "float"},
                            "target_group": {"type": "keyword"}
                        }
                    },
                    "other_ingredients": {"type": "text"},
                    "label_statements": {
                        "type": "nested",
                        "properties": {
                            "type": {"type": "keyword"},
                            "statement": {"type": "text"}
                        }
                    },
                    "company": {
                        "properties": {
                            "name": {"type": "keyword"},
                            "city": {"type": "keyword"},
                            "state": {"type": "keyword"},
                            "country": {"type": "keyword"}
                        }
                    },
                    "all_ingredients": {"type": "text"},
                    "health_benefits": {"type": "text"},
                    "warnings_precautions": {"type": "text"}
                }
            }
        }
        
        # Delete index if exists
        if self.es.indices.exists(index="supplements"):
            self.es.indices.delete(index="supplements")
            
        # Create new index
        self.es.indices.create(index="supplements", body=mapping)
        logger.info("Created supplements index with mapping")
    
    def load_excel_files(self, data_directory):
        """Load all Excel files from directory"""
        files = {
            'product_overview': 'Product_Overview.xlsx',
            'dietary_facts': 'Dietary_Supplement_Facts.xlsx',
            'other_ingredients': 'Other_Ingredients.xlsx',
            'label_statements': 'Label_Statements.xlsx',
            'company_info': 'Company_Information.xlsx'
        }
        
        dataframes = {}
        for key, filename in files.items():
            filepath = os.path.join(data_directory, filename)
            if os.path.exists(filepath):
                dataframes[key] = pd.read_excel(filepath)
                logger.info(f"Loaded {filename}: {len(dataframes[key])} rows")
            else:
                logger.warning(f"File not found: {filepath}")
                
        return dataframes
    
    def prepare_document(self, dsld_id, dataframes):
        """Prepare a single supplement document"""
        try:
            # Get main product info
            product_df = dataframes['product_overview']
            product = product_df[product_df['DSLD ID'] == dsld_id].iloc[0]
            
            # Get active ingredients
            dietary_df = dataframes.get('dietary_facts', pd.DataFrame())
            ingredients = dietary_df[dietary_df['DSLD ID'] == dsld_id] if not dietary_df.empty else pd.DataFrame()
            
            active_ingredients = []
            for _, ing in ingredients.iterrows():
                active_ingredients.append({
                    "name": str(ing['Ingredient']) if pd.notna(ing['Ingredient']) else "",
                    "category": str(ing['DSLD Ingredient Categories']) if pd.notna(ing['DSLD Ingredient Categories']) else "",
                    "amount": float(ing['Amount Per Serving']) if pd.notna(ing['Amount Per Serving']) and str(ing['Amount Per Serving']).replace('.','').isdigit() else None,
                    "unit": str(ing['Amount Per Serving Unit']) if pd.notna(ing['Amount Per Serving Unit']) else "",
                    "daily_value_percent": float(ing['% Daily Value per Serving']) if pd.notna(ing['% Daily Value per Serving']) and str(ing['% Daily Value per Serving']).replace('.','').isdigit() else None,
                    "target_group": str(ing['Daily Value Target Group']) if pd.notna(ing['Daily Value Target Group']) else ""
                })
            
            # Get other ingredients
            other_df = dataframes.get('other_ingredients', pd.DataFrame())
            other_ing = other_df[other_df['DSLD ID'] == dsld_id] if not other_df.empty else pd.DataFrame()
            other_ingredients_text = other_ing['Other Ingredients'].iloc[0] if len(other_ing) > 0 and pd.notna(other_ing['Other Ingredients'].iloc[0]) else ""
            
            # Get label statements
            statements_df = dataframes.get('label_statements', pd.DataFrame())
            statements = statements_df[statements_df['DSLD ID'] == dsld_id] if not statements_df.empty else pd.DataFrame()
            
            label_statements_list = []
            health_benefits = ""
            warnings_precautions = ""
            
            for _, stmt in statements.iterrows():
                if pd.notna(stmt['Statement']):
                    statement_obj = {
                        "type": str(stmt['Statement Type']) if pd.notna(stmt['Statement Type']) else "",
                        "statement": str(stmt['Statement'])
                    }
                    label_statements_list.append(statement_obj)
                    
                    # Extract specific types for search optimization
                    if stmt['Statement Type'] in ['Formulation', 'Other']:
                        health_benefits += " " + str(stmt['Statement'])
                    elif stmt['Statement Type'] == 'Precautions':
                        warnings_precautions += " " + str(stmt['Statement'])
            
            # Get company info
            company_df = dataframes.get('company_info', pd.DataFrame())
            company_data = company_df[company_df['DSLD ID'] == dsld_id] if not company_df.empty else pd.DataFrame()
            
            company = {}
            if len(company_data) > 0:
                company_row = company_data.iloc[0]
                company = {
                    "name": str(company_row['Company Name']) if pd.notna(company_row['Company Name']) else "",
                    "city": str(company_row['City']) if pd.notna(company_row['City']) else "",
                    "state": str(company_row['State']) if pd.notna(company_row['State']) else "",
                    "country": str(company_row['Country']) if pd.notna(company_row['Country']) else ""
                }
            
            # Combine all ingredients for search
            all_ingredients = " ".join([ing['name'] for ing in active_ingredients]) + " " + other_ingredients_text
            
            # Build final document
            document = {
                "dsld_id": str(dsld_id),
                "url": str(product['URL']) if pd.notna(product['URL']) else "",
                "product_name": str(product['Product Name']) if pd.notna(product['Product Name']) else "",
                "brand_name": str(product['Brand Name']) if pd.notna(product['Brand Name']) else "",
                "bar_code": str(product['Bar Code']) if pd.notna(product['Bar Code']) else "",
                "net_contents": str(product['Net Contents']) if pd.notna(product['Net Contents']) else "",
                "serving_size": str(product['Serving Size']) if pd.notna(product['Serving Size']) else "",
                "product_type": str(product['Product Type [LanguaL]']) if pd.notna(product['Product Type [LanguaL]']) else "",
                "supplement_form": str(product['Supplement Form [LanguaL]']) if pd.notna(product['Supplement Form [LanguaL]']) else "",
                "date_entered": str(product['Date Entered into DSLD']) if pd.notna(product['Date Entered into DSLD']) else "",
                "market_status": str(product['Market Status']) if pd.notna(product['Market Status']) else "",
                "suggested_use": str(product['Suggested Use']) if pd.notna(product['Suggested Use']) else "",
                "active_ingredients": active_ingredients,
                "other_ingredients": other_ingredients_text,
                "label_statements": label_statements_list,
                "company": company,
                "all_ingredients": all_ingredients.strip(),
                "health_benefits": health_benefits.strip(),
                "warnings_precautions": warnings_precautions.strip()
            }
            
            return document
            
        except Exception as e:
            logger.error(f"Error processing DSLD ID {dsld_id}: {e}")
            return None
    
    def bulk_import(self, data_directory, batch_size=1000):
        """Import all supplements to Elasticsearch"""
        # Load data
        dataframes = self.load_excel_files(data_directory)
        
        if 'product_overview' not in dataframes:
            raise ValueError("Product overview file is required")
        
        # Get all unique DSLD IDs
        unique_ids = dataframes['product_overview']['DSLD ID'].unique()
        total_products = len(unique_ids)
        
        logger.info(f"Starting import of {total_products} supplements")
        
        def doc_generator():
            for i, dsld_id in enumerate(unique_ids):
                doc = self.prepare_document(dsld_id, dataframes)
                if doc:
                    yield {
                        "_index": "supplements",
                        "_id": dsld_id,
                        "_source": doc
                    }
                
                if (i + 1) % 1000 == 0:
                    logger.info(f"Processed {i + 1}/{total_products} supplements")
        
        # Bulk import
        success_count = 0
        error_count = 0
        
        for success, info in bulk(self.es, doc_generator(), chunk_size=batch_size):
            if success:
                success_count += 1
            else:
                error_count += 1
                logger.error(f"Failed to index document: {info}")
        
        logger.info(f"Import completed: {success_count} successful, {error_count} failed")
        return success_count, error_count

# Usage
if __name__ == "__main__":
    importer = DSLDImporter()
    
    # Create index
    importer.create_index_mapping()
    
    # Import data (adjust path to your Excel files)
    data_directory = "../../data/excel_files"
    success, failed = importer.bulk_import(data_directory)
    
    print(f"Import completed: {success} documents indexed, {failed} failed")
