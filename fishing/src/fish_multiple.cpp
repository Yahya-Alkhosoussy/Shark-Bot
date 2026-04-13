#include <pybind11/pybind11.h>

int basic_cpp_function() {
    return 0;
}

// enum example
enum class Department {
    HR,
    Engineering,
    Sales,
    Marketing
};

struct Person {
    std::string name;
    std::string position;
    Department department;

    void ReassignDepartment(Department new_department);
};

void Person::ReassignDepartment(Department new_department) {
    department = new_department;
}

PYBIND11_MODULE(fish_multiple, m) {
    // function example
    m.def("basic_cpp_function", &basic_cpp_function);

    // enum example
    pybind11::enum_<Department>(m, "Department")
        .value("HR", Department::HR)
        .value("Engineering", Department::Engineering)
        .value("Sales", Department::Sales)
        .value("Marketing", Department::Marketing)
        .export_values();

    // class or structs
    pybind11::class_<Person>(m, "Person")
        .def(pybind11::init<std::string, std::string, Department>())
        .def("ReassignDepartment", &Person::ReassignDepartment)
        .def_readwrite("name", &Person::name)
        .def_readwrite("position", &Person::position)
        .def_readwrite("department", &Person::department);
}