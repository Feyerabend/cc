#ifndef RMATH_H
#define RMATH_H

typedef struct {
    float x, y, z;
} Vec3;

typedef struct {
    float m[4][4];
} Mat4;

// Vector operations
Vec3 vec3_add(Vec3 a, Vec3 b);
Vec3 vec3_sub(Vec3 a, Vec3 b);
Vec3 vec3_scale(Vec3 v, float s);
Vec3 vec3_multiply(Vec3 a, Vec3 b);
float vec3_dot(Vec3 a, Vec3 b);
Vec3 vec3_cross(Vec3 a, Vec3 b);
float vec3_length(Vec3 v);
Vec3 vec3_normalize(Vec3 v);
Vec3 vec3_clamp(Vec3 v, float min_val, float max_val);

// Matrix operations
Mat4 mat4_identity();
Mat4 mat4_multiply(Mat4 a, Mat4 b);
Vec3 mat4_transform_vec3(Mat4 m, Vec3 v);
Vec3 mat4_transform_normal(Mat4 m, Vec3 n);
Mat4 mat4_translation(float x, float y, float z);
Mat4 mat4_rotation_x(float angle);
Mat4 mat4_rotation_y(float angle);
Mat4 mat4_rotation_z(float angle);
Mat4 mat4_perspective(float fov, float aspect, float near, float far);

#endif