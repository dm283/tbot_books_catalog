create table if not exists dev_pg_1.public.books_catalog(	
	id serial primary key,
	title varchar(100) not null,
	author varchar(100) not null,
	photo varchar(100) not null,
	book_owner varchar(100) not null,
	create_date timestamp default now() not null,
	update_date timestamp default null
)
