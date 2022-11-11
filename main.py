from sensor.configuration.mongo_db_connection import MongoDBClient
from sensor.exception import SensorException
import sys
from sensor.logger import logging
from sensor.entity.config_entity import TrainingPipelineConfig,DataIngestionConfig
from sensor.pipeline.training_pipeline import TrainPipeline
from sensor.utils.main_utils import read_yaml
from sensor.constant.training_pipeline import SAVED_MODEL_DIR
from fastapi import FastAPI, File, UploadFile
from sensor.constant.application import APP_HOST, APP_PORT
from starlette.responses import RedirectResponse
from uvicorn import run as app_run
from fastapi.responses import Response
from fastapi.requests import Request
from sensor.ml.model.estimator import ModelResolver,TargetValueMapping
from sensor.utils.main_utils import load_object
from fastapi.middleware.cors import CORSMiddleware
import os
import pandas as pd



app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["authentication"])
async def index():
    return RedirectResponse(url="/docs")

@app.get("/train")
async def train_route():
    try:

        train_pipeline = TrainPipeline()
        if train_pipeline.is_pipeline_running:
            return Response("Training pipeline is already running.")
        train_pipeline.run_pipeline()
        return Response("Training successful !!")
    except Exception as e:
        return Response(f"Error Occurred! {e}")

@app.get("/predict")
async def predict_route(request:Request,file: UploadFile = File(...)):
    try:
        #get data from user csv file
        #conver csv file to dataframe
        df = pd.read_csv(file.file)
        model_resolver = ModelResolver(model_dir=SAVED_MODEL_DIR)
        if not model_resolver.is_model_exists():
            return Response("Model is not available")
        
        best_model_path = model_resolver.get_best_model_path()
        model = load_object(file_path=best_model_path)
        y_pred = model.predict(df)
        df['predicted_column'] = y_pred
        df['predicted_column'].replace(TargetValueMapping().reverse_mapping(),inplace=True)
        return df.to_html()
        #decide how to return file to user.
    
    except Exception as e:
        raise Response(f"Error Occured! {e}")

# def main():
#     try:
#         set_env_variable(env_file_path)
#         training_pipeline = TrainPipeline()
#         training_pipeline.run_pipeline()
#     except Exception as e:
#         print(e)
#         logging.exception(e)


if __name__=="__main__":
    #main()
    # set_env_variable(env_file_path)
    app_run(app, host=APP_HOST, port=APP_PORT)

# if __name__ == '__main__':
#     try:
#         train_pipeline =TrainPipeline()
#         train_pipeline.run_pipeline()
#         # training_pipeline_config = TrainingPipelineConfig()
#         # data_ingestion_config = DataIngestionConfig(training_pipeline_config=training_pipeline_config)
#         # print(data_ingestion_config.__dict__)
#     except Exception as e:
#         print(e)
#         raise SensorException(e,sys)