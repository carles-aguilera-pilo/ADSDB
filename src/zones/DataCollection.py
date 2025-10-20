from zones.AZone import AZone
from datasets import load_dataset
import os
from PIL import Image
from minio_connection import MinIOConnection


class DataCollection():
    BASE_DIR = os.getcwd().split("ADSDB")[0] + "ADSDB/"
    OUTPUT_DIR = os.path.join(BASE_DIR, "output/")

#    @classmethod
#    def wikipedia_scrapper(cls, topics):
#        for topic in topics:
#            url = 'https://en.wikipedia.org/wiki/' + topic
#            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
#            res = requests.get(url, headers={'User-Agent': user_agent})
#            soup = BeautifulSoup(res.text, 'html.parser')
#
#            data = ''
#            for p in soup.find_all('p'):
#                data += p.get_text()
#                data += '\n'
#            
#            data = data.strip()
#
#            for j in range(1, 750):
#                data = data.replace('[' + str(j) + ']', '')
#
#
#            fd = open(output_dir + "dataset2/" + topic + '.txt', 'w')
#            fd.write(data)
#            fd.close()

    @classmethod
    def collect_data(cls):
        cls.collect_images()

    @classmethod
    def collect_images(cls): 
        try:
            os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
            os.makedirs(cls.OUTPUT_DIR + f"images", exist_ok=True)
        except FileExistsError:
            pass

        ds = load_dataset("abaryan/ham10000_bbox")
        data = ds['train']
        sample_data = data.shuffle(seed=42).select(range(100))

        for item in sample_data:
            image: Image.Image = item['image']
            image_id: str = item['image_id']
            filename = f"{image_id}.jpg"
            save_path = os.path.join(cls.OUTPUT_DIR+"/images", filename)
            image.save(save_path)

    @classmethod
    def upload_data(cls):
        minio_client = MinIOConnection()
        new_bucket = "landing-zone"
        try:
            minio_client.create_bucket(Bucket=new_bucket)
        except (minio_client.exceptions.BucketAlreadyExists, minio_client.exceptions.BucketAlreadyOwnedByYou):
            print(f"Bucket '{new_bucket}' already exists")

        for dataset in os.listdir(cls.OUTPUT_DIR):
            for root, _, files in os.walk(dataset):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        minio_client.upload_file(file_path, new_bucket, file)
                    except Exception as e:
                        print(f"Failed to upload {file}: {e}")
            

