# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from __future__ import absolute_import

import os

import pytest

from sagemaker.huggingface import HuggingFace, HuggingFaceProcessor
from sagemaker.huggingface.model import HuggingFaceModel, HuggingFacePredictor
from sagemaker.utils import unique_name_from_base
from tests import integ
from tests.integ import DATA_DIR, TRAINING_DEFAULT_TIMEOUT_MINUTES
from tests.integ.timeout import timeout, timeout_and_delete_endpoint_by_name

ROLE = "SageMakerRole"


@pytest.mark.release
@pytest.mark.skipif(
    integ.test_region() in integ.TRAINING_NO_P2_REGIONS
    and integ.test_region() in integ.TRAINING_NO_P3_REGIONS,
    reason="no ml.p2 or ml.p3 instances in this region",
)
def test_framework_processing_job_with_deps(
    sagemaker_session,
    gpu_instance_type,
    huggingface_training_latest_version,
    huggingface_training_pytorch_latest_version,
    huggingface_pytorch_latest_training_py_version,
):
    with timeout(minutes=TRAINING_DEFAULT_TIMEOUT_MINUTES):
        code_path = os.path.join(DATA_DIR, "dummy_code_bundle_with_reqs")
        entry_point = "main_script.py"

        processor = HuggingFaceProcessor(
            transformers_version=huggingface_training_latest_version,
            pytorch_version=huggingface_training_pytorch_latest_version,
            py_version=huggingface_pytorch_latest_training_py_version,
            role=ROLE,
            instance_count=1,
            instance_type=gpu_instance_type,
            sagemaker_session=sagemaker_session,
            base_job_name="test-huggingface",
        )

        processor.run(
            code=entry_point,
            source_dir=code_path,
            inputs=[],
            wait=True,
        )


@pytest.mark.release
@pytest.mark.skipif(
    integ.test_region() in integ.TRAINING_NO_P2_REGIONS
    and integ.test_region() in integ.TRAINING_NO_P3_REGIONS,
    reason="no ml.p2 or ml.p3 instances in this region",
)
def test_huggingface_training(
    sagemaker_session,
    gpu_instance_type,
    huggingface_training_latest_version,
    huggingface_training_pytorch_latest_version,
    huggingface_pytorch_latest_training_py_version,
):
    with timeout(minutes=TRAINING_DEFAULT_TIMEOUT_MINUTES):
        data_path = os.path.join(DATA_DIR, "huggingface")

        hf = HuggingFace(
            py_version=huggingface_pytorch_latest_training_py_version,
            entry_point=os.path.join(data_path, "run_glue.py"),
            role="SageMakerRole",
            transformers_version=huggingface_training_latest_version,
            pytorch_version=huggingface_training_pytorch_latest_version,
            instance_count=1,
            instance_type=gpu_instance_type,
            hyperparameters={
                "model_name_or_path": "distilbert-base-cased",
                "task_name": "wnli",
                "do_train": True,
                "do_eval": True,
                "max_seq_length": 128,
                "fp16": True,
                "per_device_train_batch_size": 128,
                "output_dir": "/opt/ml/model",
            },
            sagemaker_session=sagemaker_session,
            disable_profiler=True,
        )

        train_input = hf.sagemaker_session.upload_data(
            path=os.path.join(data_path, "train"),
            key_prefix="integ-test-data/huggingface/train",
        )

        hf.fit(train_input)


@pytest.mark.release
@pytest.mark.skipif(
    integ.test_region() in integ.TRAINING_NO_P2_REGIONS
    and integ.test_region() in integ.TRAINING_NO_P3_REGIONS,
    reason="no ml.p2 or ml.p3 instances in this region",
)
def test_huggingface_training_tf(
    sagemaker_session,
    gpu_instance_type,
    huggingface_training_latest_version,
    huggingface_training_tensorflow_latest_version,
    huggingface_tensorflow_latest_training_py_version,
):
    with timeout(minutes=TRAINING_DEFAULT_TIMEOUT_MINUTES):
        data_path = os.path.join(DATA_DIR, "huggingface")

        hf = HuggingFace(
            py_version=huggingface_tensorflow_latest_training_py_version,
            entry_point=os.path.join(data_path, "run_tf.py"),
            role=ROLE,
            transformers_version=huggingface_training_latest_version,
            tensorflow_version=huggingface_training_tensorflow_latest_version,
            instance_count=1,
            instance_type=gpu_instance_type,
            hyperparameters={
                "model_name_or_path": "distilbert-base-cased",
                "per_device_train_batch_size": 128,
                "per_device_eval_batch_size": 128,
                "output_dir": "/opt/ml/model",
                "overwrite_output_dir": True,
                "save_steps": 5500,
            },
            sagemaker_session=sagemaker_session,
            disable_profiler=True,
        )

        train_input = hf.sagemaker_session.upload_data(
            path=os.path.join(data_path, "train"), key_prefix="integ-test-data/huggingface/train"
        )

        hf.fit(train_input)


@pytest.mark.skip(
    reason="need to re enable it later",
)
def test_huggingface_inference(
    sagemaker_session,
    gpu_instance_type,
    huggingface_inference_latest_version,
    huggingface_inference_pytorch_latest_version,
    huggingface_pytorch_latest_inference_py_version,
):
    env = {
        "HF_MODEL_ID": "philschmid/tiny-distilbert-classification",
        "HF_TASK": "text-classification",
    }
    endpoint_name = unique_name_from_base("test-hf-inference")

    model = HuggingFaceModel(
        sagemaker_session=sagemaker_session,
        role="SageMakerRole",
        env=env,
        py_version=huggingface_pytorch_latest_inference_py_version,
        transformers_version=huggingface_inference_latest_version,
        pytorch_version=huggingface_inference_pytorch_latest_version,
    )
    with timeout_and_delete_endpoint_by_name(endpoint_name, sagemaker_session):
        model.deploy(
            instance_type=gpu_instance_type, initial_instance_count=1, endpoint_name=endpoint_name
        )

        predictor = HuggingFacePredictor(endpoint_name=endpoint_name)
        data = {
            "inputs": "Camera - You are awarded a SiPix Digital Camera!"
            "call 09061221066 fromm landline. Delivery within 28 days."
        }
        output = predictor.predict(data)
        assert "score" in output[0]
