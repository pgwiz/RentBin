pkg update && pkg upgrade -y
pkg install python python-pip mariadb

# Set environment variables for proper compilation
export LDFLAGS="-L/data/data/com.termux/files/usr/lib"
export CFLAGS="-I/data/data/com.termux/files/usr/include"

# Install required libraries for image processing (Pillow dependencies)
pkg install libjpeg-turbo libpng zlib

# Set up Python virtual environment
python -m venv ~/.venv
source ~/.venv/bin/activate

#cd to phone root
cd storage/shared

git clone https://github.com/pgwiz/RentBin RentBin
cd RentBin

# Install project dependencies
pip install -r requirements.txt 

# Install additional dependencies separately
pip install wheel pymysql mysqlclient tzdata

# Run Django commands
python manage.py makemigrations
python manage.py migrate
python manage.py runserver