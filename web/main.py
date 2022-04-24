from typing import Dict, Union

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def get_root(a: int, b: str) -> Dict[str, Union[str, int]]:
    return {"a": a, "b": b}
