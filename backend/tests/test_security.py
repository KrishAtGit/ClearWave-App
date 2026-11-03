from app.security import hash_token, new_token

def test_tokens_are_unique_and_long() -> None:
    tokens = {new_token() for _ in range(1000)}
    assert len(tokens) == 1000                 
    assert all(len(t) >= 43 for t in tokens)   


def test_hash_is_stable_and_hides_the_token() -> None:
    token = new_token()
    assert hash_token(token) == hash_token(token)   
    assert hash_token(token) != token               
    assert len(hash_token(token)) == 64             
    assert hash_token(token) != hash_token(new_token()) 