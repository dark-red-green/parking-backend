# parking-backend

Run with 'flask run'.
Then send GET request to 'http://127.0.0.1:5000/img/{camera_number}/{4 character time}'. Ex: 'http://127.0.0.1:5000/img/2/0840'.
To get number of open parking spots, send GET request to 'http://127.0.0.1:5000/num_spaces/{camera_number}/{4 character time}'. Ex: 'http://localhost:5000/num_spaces/1/0909'.