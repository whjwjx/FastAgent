-- FastAIStack Database Schema Export

CREATE TABLE users (
	id SERIAL NOT NULL, 
	username VARCHAR, 
	email VARCHAR, 
	hashed_password VARCHAR, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE TABLE thoughts (
	id SERIAL NOT NULL, 
	content TEXT NOT NULL, 
	user_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE schedules (
	id SERIAL NOT NULL, 
	title VARCHAR, 
	description TEXT, 
	start_time TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	end_time TIMESTAMP WITHOUT TIME ZONE, 
	user_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Note: This schema is generated for PostgreSQL deployment.
