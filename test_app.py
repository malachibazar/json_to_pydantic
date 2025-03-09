import json
from main import generate_pydantic_model


def test_simple_model_generation():
    """Test generating a simple Pydantic model from JSON"""
    sample_json = {
        "name": "John Doe",
        "age": 30,
        "email": "john@example.com",
        "is_active": True,
    }

    model = generate_pydantic_model(sample_json)
    print("\nSimple model test:")
    print(model)

    # Basic assertions to verify the model
    assert "class MyModel(BaseModel):" in model
    assert "name: str" in model
    assert "age: int" in model
    assert "email: str" in model
    assert "is_active: bool" in model


def test_nested_model_generation():
    """Test generating a model with nested objects"""
    sample_json = {
        "user_id": 1234,
        "username": "johndoe",
        "profile": {"full_name": "John Doe", "bio": "Software developer", "age": 30},
    }

    model = generate_pydantic_model(sample_json)
    print("\nNested model test:")
    print(model)

    # Verify nested model creation
    assert "class Profile(BaseModel):" in model
    assert "full_name: str" in model
    assert "class MyModel(BaseModel):" in model
    assert "profile: Profile" in model


def test_list_model_generation():
    """Test generating a model with lists"""
    sample_json = {
        "title": "My Post",
        "tags": ["python", "fastapi", "pydantic"],
        "comments": [
            {"id": 1, "text": "Great post!", "author": "user1"},
            {"id": 2, "text": "Thanks for sharing", "author": "user2"},
        ],
    }

    model = generate_pydantic_model(sample_json)
    print("\nList model test:")
    print(model)

    # Verify list handling
    assert "tags: list[str]" in model
    assert "class Comment(BaseModel):" in model
    assert "comments: list[Comment]" in model


def test_date_time_detection():
    """Test detection of date and datetime values"""
    sample_json = {
        "create_date": "2023-01-01",
        "update_date": "2023-01-15",
        "last_login": "2023-01-15T14:30:45Z",
        "published_at": "2023-01-15 14:30:45",
        "expires_on": "01/15/2023",
        "api_timestamp": "Mon, 15 Jan 2023 14:30:45 GMT",
    }

    model = generate_pydantic_model(sample_json)
    print("\nDate/time detection test:")
    print(model)

    # Check for date/datetime imports
    assert "from datetime import date, datetime" in model

    # Check for date fields
    assert "create_date: date" in model
    assert "update_date: date" in model
    assert "expires_on: date" in model

    # Check for datetime fields
    assert "last_login: datetime" in model
    assert "published_at: datetime" in model
    assert "api_timestamp: datetime" in model


def test_optional_fields():
    """Test generating a model with optional fields"""
    sample_json = {
        "name": "John Doe",
        "age": 30,
        "email": "john@example.com",
    }

    model = generate_pydantic_model(sample_json, make_optional=True)
    print("\nOptional fields test:")
    print(model)

    # Verify optional fields
    assert "name: str | None = None" in model
    assert "age: int | None = None" in model
    assert "email: str | None = None" in model


def test_camel_case_conversion():
    """Test converting camelCase to snake_case with aliases"""
    sample_json = {
        "userId": 1234,
        "userName": "johndoe",
        "userProfile": {"fullName": "John Doe", "userAge": 30},
    }

    model = generate_pydantic_model(sample_json, convert_camel_case=True)
    print("\nCamelCase conversion test:")
    print(model)

    # Verify camelCase conversion
    assert "user_id: int = Field(alias='userId')" in model
    assert "user_name: str = Field(alias='userName')" in model
    assert "full_name: str = Field(alias='fullName')" in model
    assert "user_age: int = Field(alias='userAge')" in model
    assert "model_config = ConfigDict(populate_by_name=True)" in model
    assert "class Config:" not in model


def test_complex_model_generation():
    """Test generating a complex model with nested objects and lists"""
    sample_json = {
        "user_id": 1234,
        "username": "johndoe",
        "email": "john@example.com",
        "is_active": True,
        "profile": {
            "full_name": "John Doe",
            "bio": "Software developer",
            "age": 30,
            "interests": ["coding", "hiking", "reading"],
        },
        "posts": [
            {
                "id": 1,
                "title": "Hello World",
                "content": "This is my first post",
                "tags": ["programming", "intro"],
            },
            {
                "id": 2,
                "title": "Pydantic is awesome",
                "content": "Here's why I love Pydantic",
                "tags": ["python", "pydantic", "coding"],
            },
        ],
        "last_login": "2023-01-15T14:30:45Z",
        "created_date": "2023-01-01",
        "metadata": None,
    }

    model = generate_pydantic_model(sample_json)
    print("\nComplex model test:")
    print(model)

    # Verify complex model creation
    assert "class Profile(BaseModel):" in model
    assert "interests: list[str]" in model
    assert "class Post(BaseModel):" in model
    assert "tags: list[str]" in model
    assert "posts: list[Post]" in model
    assert "last_login: datetime" in model
    assert "created_date: date" in model
    assert "metadata: None" in model


def test_combined_options():
    """Test using both options together"""
    sample_json = {
        "userId": 1234,
        "userName": "johndoe",
        "userPosts": [{"postId": 1, "postTitle": "Hello World"}],
        "lastLoginDate": "2023-01-15T14:30:45Z",
    }

    model = generate_pydantic_model(
        sample_json, make_optional=True, convert_camel_case=True
    )
    print("\nCombined options test:")
    print(model)

    # Check for individual elements instead of exact format
    assert "user_id:" in model
    assert "| None = None" in model
    assert "Field(alias='userId')" in model
    assert "user_name:" in model
    assert "Field(alias='userName')" in model
    assert "post_id:" in model
    assert "Field(alias='postId')" in model
    assert "post_title:" in model
    assert "Field(alias='postTitle')" in model
    assert "last_login_date: datetime | None = None" in model
    assert "Field(alias='lastLoginDate')" in model
    assert "model_config = ConfigDict(populate_by_name=True)" in model
    assert "class Config:" not in model


if __name__ == "__main__":
    # Run all tests
    test_simple_model_generation()
    test_nested_model_generation()
    test_list_model_generation()
    test_date_time_detection()
    test_optional_fields()
    test_camel_case_conversion()
    test_complex_model_generation()
    test_combined_options()

    print("\nAll tests passed successfully!")
