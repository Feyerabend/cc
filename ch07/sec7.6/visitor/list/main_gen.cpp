#include <iostream>
#include <functional>

template<typename T>
class Gardener {
private:
    struct Node {
        T data;
        Node* next;
        Node(const T& value, Node* n = nullptr)
            : data(value), next(n) {}
    };

    Node* head = nullptr;

public:
    ~Gardener() {
        clear();
    }

    void push_front(const T& value) {
        head = new Node(value, head);
    }

    void push_back(const T& value) {
        Node** current = &head;
        while (*current)
            current = &((*current)->next);

        *current = new Node(value);
    }

    void remove(const T& value) {
        Node** current = &head;
        while (*current) {
            if ((*current)->data == value) {
                Node* temp = *current;
                *current = temp->next;
                delete temp;
                return;
            }
            current = &((*current)->next);
        }
    }

    void replace(const T& old_value, const T& new_value) {
        Node* current = head;
        while (current) {
            if (current->data == old_value) {
                current->data = new_value;
                return;
            }
            current = current->next;
        }
    }

    void print_all(std::function<void(const T&)> printer) const {
        Node* current = head;
        while (current) {
            printer(current->data);
            current = current->next;
        }
    }

    void clear() {
        while (head) {
            Node* temp = head;
            head = head->next;
            delete temp;
        }
    }
};


int main() {
    Gardener<std::string> g;

    g.push_front("1");
    g.push_front("2");
    g.push_front("3");
    g.push_back("4");

    g.print_all([](const std::string& s) {
        std::cout << s << "\n";
    });

    g.replace("1", "0");
    g.remove("2");

    return 0;
}
