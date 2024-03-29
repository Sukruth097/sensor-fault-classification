from sensor.exception import SensorException
from sensor.logger import logging
import pandas as pd
import numpy as np
import os,sys
from imblearn.combine import SMOTETomek
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler
from sklearn.pipeline import Pipeline
from sensor.constant.training_pipeline import TARGET_COLUMN
from sensor.entity.artifact_entity import DataValidationArtifact,DataTransformationArtifact
from sensor.entity.config_entity import DataTransformationConfig
from sensor.utils.main_utils import save_numpy_array_data,load_numpy_array_data,save_object
from sensor.ml.model.estimator import TargetValueMapping

class DataTransformation:

    def __init__(self,data_validation_artifact:DataValidationArtifact,
                 data_transformation_config: DataTransformationConfig):

        """
        :param data_validation_artifact: Output reference of data ingestion artifact stage
        :param data_transformation_config: configuration for data transformation

        """
        try:
            self.data_validation_artifact = data_validation_artifact
            self.data_transformation_config = data_transformation_config

        except Exception as e:
            raise SensorException(e, sys)

    @staticmethod
    def read_data(file_path) ->pd.DataFrame:
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise SensorException(e,sys)

    def get_data_transformer_object(cls) ->Pipeline:

        """
        In Pipeline we followd 2 steps:
        1st step: fill missing values with 0 using SimpleImputer
        2nd step: Use Robust Scaler to remove outliers and normalize the data 
        These 2 steps will be converted to pickle, so for new data we dont need to write this 
        repetative code instead we can use this function and complete the preprocessing of data
        """

        try:
            robust_scaler = RobustScaler()
            simple_imputer = SimpleImputer(strategy='constant',fill_value=0)
            preprocessor = Pipeline(
                steps=[
                    ("Imputer", simple_imputer), #replace missing values with zero
                    ("RobustScaler", robust_scaler) #keep every feature in same range and handle outlier
                ]
            )
            return preprocessor
        except Exception as e:
            raise SensorException(e,sys)

    def initiate_data_transformation(self,) -> DataTransformationArtifact:

        try:
            logging.info(f"Data transformation Started ")
            train_df = DataTransformation.read_data(self.data_validation_artifact.valid_train_file_path)
            test_df = DataTransformation.read_data(self.data_validation_artifact.valid_test_file_path)
            preprocessor = self.get_data_transformer_object()

            #training dataframe
            input_feature_train_df = train_df.drop(columns=[TARGET_COLUMN], axis=1)
            logging.info(f"For Train the Target column {TARGET_COLUMN} is removed")
            target_feature_train_df = train_df[TARGET_COLUMN]
            target_feature_train_df = target_feature_train_df.replace( TargetValueMapping().to_dict())
            logging.info(f"The target columnsof Train Dataset is converted to numeric succesfully")
            #testing dataframe
            input_feature_test_df = test_df.drop(columns=[TARGET_COLUMN], axis=1)
            logging.info(f"For Test the Target column {TARGET_COLUMN} is removed")

            target_feature_test_df = test_df[TARGET_COLUMN]
            target_feature_test_df = target_feature_test_df.replace(TargetValueMapping().to_dict())
            logging.info(f"The target columns of Test Dataset is converted to numeric succesfully")
            

            preprocessor_object = preprocessor.fit(input_feature_train_df)
            transformed_input_train_feature = preprocessor_object.transform(input_feature_train_df)
            transformed_input_test_feature =preprocessor_object.transform(input_feature_test_df)
            logging.info(f"Succesfully Completed Preprocessing Steps")
            
            smt = SMOTETomek(sampling_strategy='minority')
            logging.info(f"Balancing the Dataset Using SMOTETomek method has started")


            input_feature_train_final, target_feature_train_final = smt.fit_resample(
                transformed_input_train_feature, target_feature_train_df
            )

            input_feature_test_final, target_feature_test_final = smt.fit_resample(
                transformed_input_test_feature, target_feature_test_df
            )
            logging.info(f"Balancing the Dataset Using SMOTETomek method has Completed")
            
            train_arr = np.c_[input_feature_train_final, np.array(target_feature_train_final) ]
            test_arr = np.c_[ input_feature_test_final, np.array(target_feature_test_final) ]

            #save numpy array data
            logging.info(f" Starting the conversion of data to numpy array")
            save_numpy_array_data( self.data_transformation_config.transformed_train_file_path, array=train_arr, )
            save_numpy_array_data( self.data_transformation_config.transformed_test_file_path,array=test_arr,)
            save_object( self.data_transformation_config.transformed_object_file_path, preprocessor_object,)
            logging.info(f" Completed the conversion of data to numpy array")
            
            
            #preparing artifact
            data_transformation_artifact = DataTransformationArtifact(
                transformed_object_file_path=self.data_transformation_config.transformed_object_file_path,
                transformed_train_file_path=self.data_transformation_config.transformed_train_file_path,
                transformed_test_file_path=self.data_transformation_config.transformed_test_file_path,
            )
            logging.info(f"Data transformation artifact: {data_transformation_artifact}")
            logging.info(f"Data transformation Succesfully Completed ")

            return data_transformation_artifact
        except Exception as e:
            raise SensorException(e,sys)




