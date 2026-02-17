def test_performance(secrets, benchmark):
    def access_secret_store():
        for i in range(0, 20):
            key = f"key-{i}"
            value = f"value {i}"
            secrets.save(key, value)
            assert value == secrets.get(key)

    benchmark.pedantic(access_secret_store, iterations=1, rounds=15)
