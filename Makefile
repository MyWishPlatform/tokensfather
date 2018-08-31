NAME=eosio.token

all:
	rm -rf $(NAME)/$(NAME).wasm
	rm -rf $(NAME)/$(NAME).wast
	eosiocpp -o $(NAME)/$(NAME).wast $(NAME).cpp

test:
	python3 unittest_eosiotoken.py
