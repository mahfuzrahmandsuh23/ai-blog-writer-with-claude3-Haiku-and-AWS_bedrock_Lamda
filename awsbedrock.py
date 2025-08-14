import boto3
import botocore.config
import json
from datetime import datetime

def blog_generate_using_bedrock(blogtopic: str) -> str:
    # Improved prompt for better response
    user_text = (
        f"You are a professional content writer. Write a detailed 200-word blog post on the topic: '{blogtopic}'. "
        "Use a hook in the introduction and end with a clear conclusion or takeaway message."
    )

    # Claude 3 Haiku request payload
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "temperature": 0.5,
        "top_p": 0.9,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": user_text}]}
        ]
    }

    try:
        bedrock = boto3.client(
            "bedrock-runtime",
            region_name="us-east-1",
            config=botocore.config.Config(read_timeout=300, retries={"max_attempts": 3})
        )

        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps(payload)
        )

        # Parse Claude response
        resp = json.loads(response["body"].read())
        print("Claude raw response:", json.dumps(resp, indent=2))  # For debugging

        if "content" in resp and resp["content"]:
            blog_details = resp["content"][0]["text"]
            print("Generated Blog:\n", blog_details)
            return blog_details
        else:
            print("No content returned by Claude.")
            return ""

    except Exception as e:
        print(f"Error generating the blog: {e}")
        return ""

def save_blog_details_s3(s3_key, s3_bucket, generate_blog):
    s3 = boto3.client("s3")
    try:
        s3.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=generate_blog.encode("utf-8"),
            ContentType="text/plain; charset=utf-8"
        )
        print("✅ Blog saved to S3")
    except Exception as e:
        print(f"❌ Error when saving the blog to S3: {e}")

def lambda_handler(event, context):
    try:
        event_data = json.loads(event["body"])
        blogtopic = event_data["blog_topic"]
    except (KeyError, json.JSONDecodeError) as parse_error:
        print(f"❌ Error parsing event: {parse_error}")
        return {"statusCode": 400, "body": json.dumps("Invalid input format")}

    generate_blog = blog_generate_using_bedrock(blogtopic=blogtopic)

    if generate_blog:
        current_time = datetime.now().strftime("%H%M%S")
        s3_key = f"blog-output/{current_time}.txt"
        s3_bucket = "mahibucklamda25"
        save_blog_details_s3(s3_key, s3_bucket, generate_blog)
    else:
        print("❌ No blog was generated")

    return {
        "statusCode": 200,
        "body": json.dumps("✅ Blog generation completed")
    }
