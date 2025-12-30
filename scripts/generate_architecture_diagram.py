#!/usr/bin/env python3
"""
Generate AWS Architecture Diagram for AWS AutoML Lite.

Requirements:
    pip install diagrams

    Also requires Graphviz installed:
    - Windows: choco install graphviz OR https://graphviz.org/download/
    - Mac: brew install graphviz
    - Linux: apt-get install graphviz

Usage:
    python scripts/generate_architecture_diagram.py

Output:
    Creates 6 PNG files in the docs/diagrams/ directory:
    - architecture-main.png
    - architecture-dataflow.png
    - architecture-inference.png (NEW in v1.1.0)
    - architecture-cost.png
    - architecture-cicd.png
    - architecture-training.png
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda, Batch, Fargate
from diagrams.aws.database import Dynamodb
from diagrams.aws.storage import S3
from diagrams.aws.network import APIGateway
from diagrams.aws.management import Cloudwatch
from diagrams.aws.mobile import Amplify
from diagrams.aws.ml import Sagemaker
from diagrams.onprem.client import User
import os

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "docs", "diagrams")

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Common graph attributes for better readability
GRAPH_ATTR = {
    "fontsize": "18",
    "fontname": "Arial Bold",
    "bgcolor": "white",
    "pad": "0.4",
    "splines": "ortho",
    "nodesep": "0.8",
    "ranksep": "1.0",
}

# Node attributes - BIGGER and BOLDER fonts
NODE_ATTR = {
    "fontsize": "13",
    "fontname": "Arial Bold",
    "fontcolor": "#333333",
}

# Edge attributes
EDGE_ATTR = {
    "fontsize": "12",
    "fontname": "Arial Bold",
    "fontcolor": "#333333",
    "penwidth": "2.0",
}

# Cluster attributes
CLUSTER_ATTR = {
    "fontsize": "14",
    "fontname": "Arial Bold",
    "fontcolor": "#1a1a1a",
    "style": "rounded",
    "bgcolor": "#e8f4fc",
    "penwidth": "2",
}


def create_main_architecture():
    """Create the main architecture diagram - HORIZONTAL layout."""
    
    with Diagram(
        "AWS AutoML Lite",
        show=False,
        filename=os.path.join(OUTPUT_DIR, "architecture-main"),
        outformat="png",
        graph_attr=GRAPH_ATTR,
        node_attr=NODE_ATTR,
        edge_attr=EDGE_ATTR,
        direction="LR"
    ):
        user = User("User")
        
        # Frontend
        amplify = Amplify("Amplify\nNext.js SSR")
        
        # API Layer
        with Cluster("API Layer", graph_attr=CLUSTER_ATTR):
            api_gw = APIGateway("API Gateway")
            lambda_fn = Lambda("FastAPI\n+ ONNX Inference")
        
        # Storage
        with Cluster("Storage", graph_attr=CLUSTER_ATTR):
            dynamo = Dynamodb("DynamoDB")
            s3 = S3("S3 Buckets")
        
        # Training
        with Cluster("Training (Fargate Spot)", graph_attr=CLUSTER_ATTR):
            batch = Batch("AWS Batch")
            fargate = Fargate("Container\n(265MB)")
        
        # Monitoring
        logs = Cloudwatch("Logs")
        
        # Flow - horizontal
        user >> amplify >> api_gw >> lambda_fn
        lambda_fn >> dynamo
        lambda_fn >> s3
        lambda_fn >> batch >> fargate
        fargate >> s3
        fargate >> dynamo
        fargate >> logs


def create_data_flow_diagram():
    """Create the data flow diagram - 5 phases horizontal (updated v1.1.0)."""
    
    with Diagram(
        "Data Flow: Upload → Train → Predict",
        show=False,
        filename=os.path.join(OUTPUT_DIR, "architecture-dataflow"),
        outformat="png",
        graph_attr=GRAPH_ATTR,
        node_attr=NODE_ATTR,
        edge_attr=EDGE_ATTR,
        direction="LR"
    ):
        user = User("User")
        
        # Phase 1: Upload
        with Cluster("1. Upload", graph_attr=CLUSTER_ATTR):
            s3_upload = S3("S3")
        
        # Phase 2: Configure  
        with Cluster("2. Analyze", graph_attr=CLUSTER_ATTR):
            lambda_fn = Lambda("Lambda")
            dynamo_meta = Dynamodb("Metadata")
        
        # Phase 3: Train
        with Cluster("3. Train", graph_attr=CLUSTER_ATTR):
            fargate = Fargate("FLAML\nTraining")
        
        # Phase 4: Results
        with Cluster("4. Results", graph_attr=CLUSTER_ATTR):
            s3_model = S3(".pkl + .onnx")
            dynamo_metrics = Dynamodb("Metrics")
        
        # Phase 5: Predict (NEW in v1.1.0)
        with Cluster("5. Predict", graph_attr=CLUSTER_ATTR):
            lambda_inference = Lambda("ONNX\nRuntime")
        
        # Linear flow
        user >> Edge(label="CSV", fontsize="13", fontname="Arial Bold") >> s3_upload
        s3_upload >> lambda_fn >> dynamo_meta
        dynamo_meta >> fargate
        fargate >> s3_model
        fargate >> dynamo_metrics
        s3_model >> lambda_inference
        lambda_inference >> Edge(label="Prediction", fontsize="13", fontname="Arial Bold") >> user


def create_cost_comparison_diagram():
    """Create cost comparison - side by side layout."""
    
    cost_graph_attr = {
        "fontsize": "18",
        "fontname": "Arial Bold",
        "bgcolor": "white",
        "pad": "0.6",
        "splines": "ortho",
        "nodesep": "1.2",
        "ranksep": "0.8",
    }
    
    sagemaker_cluster = {
        "fontsize": "15",
        "fontname": "Arial Bold",
        "fontcolor": "#1a1a1a",
        "style": "rounded",
        "bgcolor": "#fce8e8",  # Light red for expensive
        "penwidth": "2",
    }
    
    automl_cluster = {
        "fontsize": "15",
        "fontname": "Arial Bold", 
        "fontcolor": "#1a1a1a",
        "style": "rounded",
        "bgcolor": "#e8fce8",  # Light green for cheap
        "penwidth": "2",
    }
    
    with Diagram(
        "Cost: SageMaker (with endpoint) vs AutoML Lite",
        show=False,
        filename=os.path.join(OUTPUT_DIR, "architecture-cost"),
        outformat="png",
        graph_attr=cost_graph_attr,
        node_attr=NODE_ATTR,
        edge_attr=EDGE_ATTR,
        direction="LR"  # Horizontal side by side
    ):
        with Cluster("SageMaker AI\n$36-171/mo (idle)", graph_attr=sagemaker_cluster):
            sm_studio = Sagemaker("Training\n($0.03-0.16/job)")
            sm_endpoint = Sagemaker("Endpoint\n$36-171/mo\n(idle)")
            sm_studio - sm_endpoint
        
        with Cluster("AutoML Lite (Scale-to-zero)\n~$3-25/mo ($0 idle)", graph_attr=automl_cluster):
            lite_amplify = Amplify("Amplify\n(Next.js SSR)")
            lite_lambda = Lambda("API + Inference\n$0 idle\n(~$0.000004/req)")
            lite_fargate = Fargate("Batch (Spot)\n$0.02/job")
            lite_amplify - lite_lambda - lite_fargate


def create_cicd_diagram():
    """Create CI/CD pipeline diagram."""
    from diagrams.onprem.vcs import Github
    from diagrams.aws.devtools import Codebuild
    from diagrams.generic.blank import Blank
    
    cicd_graph_attr = {
        "fontsize": "16",
        "fontname": "Arial Bold",
        "bgcolor": "white",
        "pad": "0.4",
        "splines": "ortho",
        "nodesep": "0.6",
        "ranksep": "0.8",
    }
    
    with Diagram(
        "CI/CD: GitHub Actions + OIDC",
        show=False,
        filename=os.path.join(OUTPUT_DIR, "architecture-cicd"),
        outformat="png",
        graph_attr=cicd_graph_attr,
        node_attr=NODE_ATTR,
        edge_attr=EDGE_ATTR,
        direction="LR"
    ):
        github = Github("GitHub\nActions")
        
        with Cluster("Deploy Targets", graph_attr=CLUSTER_ATTR):
            lambda_fn = Lambda("Lambda API\n~2 min")
            ecr = Fargate("ECR Container\n~3 min")
            amplify = Amplify("Amplify\n~3 min")
        
        github >> Edge(label="OIDC", fontsize="11", fontname="Arial Bold") >> lambda_fn
        github >> ecr
        github >> amplify


def create_training_detail_diagram():
    """Create detailed training container diagram (updated v1.1.0 with ONNX)."""
    from diagrams.programming.language import Python
    from diagrams.onprem.container import Docker
    
    training_graph_attr = {
        "fontsize": "16",
        "fontname": "Arial Bold",
        "bgcolor": "white",
        "pad": "0.4",
        "splines": "ortho",
        "nodesep": "0.7",
        "ranksep": "0.9",
    }
    
    with Diagram(
        "Training Container Flow (v1.1.0)",
        show=False,
        filename=os.path.join(OUTPUT_DIR, "architecture-training"),
        outformat="png",
        graph_attr=training_graph_attr,
        node_attr=NODE_ATTR,
        edge_attr=EDGE_ATTR,
        direction="LR"
    ):
        batch = Batch("AWS Batch\nTrigger")
        
        with Cluster("Fargate Spot Container (265MB)", graph_attr=CLUSTER_ATTR):
            download = S3("Download\nCSV")
            eda = Dynamodb("Generate\nEDA")
            train = Fargate("FLAML\nTraining")
            onnx_export = Fargate("ONNX\nExport")
            
        with Cluster("Outputs", graph_attr=CLUSTER_ATTR):
            model_pkl = S3("Model .pkl")
            model_onnx = S3("Model .onnx")
            report = S3("Reports")
            metrics = Dynamodb("Metrics")
        
        batch >> download >> eda >> train >> onnx_export
        onnx_export >> model_pkl
        onnx_export >> model_onnx
        train >> report
        train >> metrics


def create_inference_diagram():
    """Create serverless inference architecture diagram (NEW in v1.1.0)."""
    
    inference_graph_attr = {
        "fontsize": "16",
        "fontname": "Arial Bold",
        "bgcolor": "white",
        "pad": "0.4",
        "splines": "ortho",
        "nodesep": "0.8",
        "ranksep": "1.0",
    }
    
    inference_cluster = {
        "fontsize": "14",
        "fontname": "Arial Bold",
        "fontcolor": "#1a1a1a",
        "style": "rounded",
        "bgcolor": "#e8fce8",  # Light green for serverless
        "penwidth": "2",
    }
    
    with Diagram(
        "Serverless Inference (v1.1.0)",
        show=False,
        filename=os.path.join(OUTPUT_DIR, "architecture-inference"),
        outformat="png",
        graph_attr=inference_graph_attr,
        node_attr=NODE_ATTR,
        edge_attr=EDGE_ATTR,
        direction="LR"
    ):
        user = User("User")
        
        # Frontend
        amplify = Amplify("Playground UI")
        
        # API Layer
        with Cluster("Serverless Inference", graph_attr=inference_cluster):
            api_gw = APIGateway("API Gateway\n/predict/{job_id}")
            lambda_fn = Lambda("Lambda\nONNX Runtime")
        
        # Storage
        with Cluster("Model Storage", graph_attr=CLUSTER_ATTR):
            s3_onnx = S3("model.onnx")
            dynamo = Dynamodb("Job Metadata\n(deployed=true)")
        
        # Flow
        user >> amplify >> api_gw >> lambda_fn
        lambda_fn >> Edge(label="Load", fontsize="11", fontname="Arial Bold") >> s3_onnx
        lambda_fn >> dynamo
        lambda_fn >> Edge(label="Prediction", fontsize="11", fontname="Arial Bold") >> user


if __name__ == "__main__":
    print("Generating architecture diagrams...")
    print(f"Output directory: {OUTPUT_DIR}")
    
    try:
        print("\n1. Creating main architecture diagram...")
        create_main_architecture()
        print("   [OK] architecture-main.png")
        
        print("\n2. Creating data flow diagram...")
        create_data_flow_diagram()
        print("   [OK] architecture-dataflow.png")
        
        print("\n3. Creating cost comparison diagram...")
        create_cost_comparison_diagram()
        print("   [OK] architecture-cost.png")
        
        print("\n4. Creating CI/CD pipeline diagram...")
        create_cicd_diagram()
        print("   [OK] architecture-cicd.png")
        
        print("\n5. Creating training container diagram...")
        create_training_detail_diagram()
        print("   [OK] architecture-training.png")
        
        print("\n6. Creating inference architecture diagram...")
        create_inference_diagram()
        print("   [OK] architecture-inference.png")
        
        print(f"\n[OK] All diagrams generated in: {OUTPUT_DIR}")
        print("\nAvailable diagrams:")
        print("  - architecture-main.png       (Main architecture overview)")
        print("  - architecture-dataflow.png   (Data flow: Upload -> Train -> Predict)")
        print("  - architecture-cost.png       (Cost comparison with SageMaker)")
        print("  - architecture-cicd.png       (CI/CD pipeline)")
        print("  - architecture-training.png   (Training container detail)")
        print("  - architecture-inference.png  (Serverless inference - v1.1.0)")
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        print("\nMake sure you have installed:")
        print("  pip install diagrams")
        print("  And Graphviz: https://graphviz.org/download/")
