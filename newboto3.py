import boto3
import botocore
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
from io import BytesIO

AWS_REGION = "us-east-1"  # <-- set this to your bucket’s region

def detect_labels(photo, bucket, region=AWS_REGION):
    try:
        # Clients/resources pinned to a region (S3+Rekognition must match the bucket’s region)
        client = boto3.client("rekognition", region_name=region)
        s3 = boto3.resource("s3", region_name=region)

        # Detect labels
        response = client.detect_labels(
            Image={"S3Object": {"Bucket": bucket, "Name": photo}},
            MaxLabels=10
        )

        print("Detected labels for " + photo)
        print()
        for label in response.get("Labels", []):
            print("Label:", label.get("Name"))
            print("Confidence:", round(label.get("Confidence", 0.0), 2))
            print()

        # Load the image from S3
        obj = s3.Object(bucket, photo)
        img_data = obj.get()["Body"].read()
        img = Image.open(BytesIO(img_data)).convert("RGB")

        # Display the image with bounding boxes
        plt.imshow(img)
        ax = plt.gca()
        for label in response.get("Labels", []):
            for instance in label.get("Instances", []):
                bbox = instance.get("BoundingBox", {})
                left   = bbox.get("Left", 0)   * img.width
                top    = bbox.get("Top", 0)    * img.height
                width  = bbox.get("Width", 0)  * img.width
                height = bbox.get("Height", 0) * img.height
                rect = patches.Rectangle(
                    (left, top), width, height,
                    linewidth=1, edgecolor="r", facecolor="none"
                )
                ax.add_patch(rect)
                label_text = f"{label.get('Name','?')} ({round(label.get('Confidence',0.0), 2)}%)"
                plt.text(left, max(0, top - 2), label_text, color="r", fontsize=8,
                         bbox=dict(facecolor="white", alpha=0.7))
        plt.axis("off")
        plt.show()

        return len(response.get("Labels", []))

    except botocore.exceptions.NoCredentialsError:
        print("ERROR: No AWS credentials found. Run `aws configure` or set env vars.")
    except botocore.exceptions.PartialCredentialsError:
        print("ERROR: Partial/invalid credentials. Re-run `aws configure`.")
    except client.exceptions.InvalidS3ObjectException as e:
        print("ERROR: Rekognition couldn’t read the S3 object. Likely region mismatch or access issue.")
        print(e)
    except client.exceptions.InvalidImageFormatException:
        print("ERROR: File isn’t a supported image format for Rekognition.")
    except botocore.exceptions.ClientError as e:
        code = e.response["Error"].get("Code", "")
        print(f"AWS ClientError: {code} -> {e}")
        if code in ("AccessDenied", "AccessDeniedException"):
            print("Check IAM permissions for rekognition:DetectLabels and s3:GetObject.")
        if code == "404" or code == "NoSuchKey":
            print("The object key is wrong or file not found in the bucket.")
    except Exception as e:
        print("Unexpected error:", repr(e))

def main():
    photo = "6c846184b13cc2564a33aea1fb23810d.jpg"
    bucket = "arekog"
    label_count = detect_labels(photo, bucket, region=AWS_REGION)
    if isinstance(label_count, int):
        print("Labels detected:", label_count)

if __name__ == "__main__":
    main()
