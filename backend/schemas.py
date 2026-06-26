# from pydantic import BaseModel
# # schemas define what data enters and leveaves the API. They are used for validation and serialization.

# # ------------------------------------------------------------------
# # USER REGISTRATION INPUT
# # ------------------------------------------------------------------
# # This schema validates incoming data.
# #
# # If client forgets a field,
# # FastAPI automatically returns an error.

# class UserCreate(BaseModel):
#     username: str
#     email: str
#     password: str

# # ------------------------------------------------------------------
# # LOGIN INPUT
# # ------------------------------------------------------------------
# class LoginRequest(BaseModel):

#     username: str
#     password: str


# # ------------------------------------------------------------------
# # OUTPUT SCHEMA
# # ------------------------------------------------------------------
# # Used when returning user information.
# # It excludes sensitive data like password.

# class UserResponse(BaseModel):
#     id: int
#     username: str
#     email: str
#     role: str

#     class Config:
#         # Allows conversion from SQLAlchemy object
#         # into Pydantic response.
#         #
#         from_attributes = True



# # Jobs schema
# class JobCreate(BaseModel):
#     title: str
#     description: str
#     required_skills: str
#     experience_level: str


# class ApplicationCreate(BaseModel):
#     candidate_id: int
#     job_id: int


from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "candidate"   # "candidate" or "hr"


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str

    class Config:
        from_attributes = True


class JobCreate(BaseModel):
    title: str
    description: str
    required_skills: str
    experience_level: str


class ApplicationCreate(BaseModel):
    # KEY FIX: candidate_id removed — resolved from JWT token in the route
    job_id: int