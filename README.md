# 🚀 Quick Start (Recommended)

1. Install Docker :-
Go to: https://www.docker.com/products/docker-desktop


2. Run Docker :-
Open Docker Desktop
Wait until it shows “Docker is running”


3.Open project cmd 

Run : docker-compose up --build

4. Open new project cmd

Run : docker exec -it yuktic_doris-updated-version-db-1 mysql -u root -p

Enter Password : root

CREATE TABLE property_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reg_no VARCHAR(50),
    reg_date DATE,
    first_party TEXT,
    second_party TEXT,
    property_address TEXT,
    area VARCHAR(100),
    deed_type TEXT,
    property_type VARCHAR(50),
    sro_name VARCHAR(150),
    locality_name VARCHAR(150),
    scrape_status ENUM('IN_PROGRESS','COMPLETED')
);


ALTER TABLE property_records
ADD UNIQUE (reg_no, sro_name, locality_name);



5. Open Applicaltion : http://localhost:3000


6. Next Time reopen :-

Just Run : docker compose up

Stop Project : docker compose down
