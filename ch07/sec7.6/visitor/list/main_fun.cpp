#include <iostream>
#include <vector>
#include <memory>
#include <functional>
#include <algorithm>

class Tree {
private:
    struct Node {
        int value;
        std::vector<std::unique_ptr<Node>> children;

        Node(int v) : value(v) {}
    };

    std::unique_ptr<Node> root;


    Node* find(Node* current, int value) {
        if (!current) return nullptr;
        if (current->value == value) return current;

        for (auto& child : current->children) {
            if (auto result = find(child.get(), value))
                return result;
        }
        return nullptr;
    }


    bool remove_node(std::vector<std::unique_ptr<Node>>& nodes, int value) {
        auto it = std::remove_if(nodes.begin(), nodes.end(),
            [value](const std::unique_ptr<Node>& n) {
                return n->value == value;
            });

        if (it != nodes.end()) {
            nodes.erase(it, nodes.end());
            return true;
        }

        for (auto& node : nodes) {
            if (remove_node(node->children, value))
                return true;
        }

        return false;
    }


    void print_node(const Node* node, int depth) const {
        if (!node) return;

        std::cout << std::string(depth * 2, ' ')
                  << node->value << "\n";

        for (const auto& child : node->children)
            print_node(child.get(), depth + 1);
    }

public:
    Tree(int root_value) {
        root = std::make_unique<Node>(root_value);
    }

    bool add(int parent_value, int new_value) {
        Node* parent = find(root.get(), parent_value);
        if (!parent) return false;

        parent->children.push_back(
            std::make_unique<Node>(new_value)
        );
        return true;
    }

    bool insert(int parent_value, int new_value, size_t index) {
        Node* parent = find(root.get(), parent_value);
        if (!parent) return false;

        if (index > parent->children.size())
            index = parent->children.size();

        parent->children.insert(
            parent->children.begin() + index,
            std::make_unique<Node>(new_value)
        );
        return true;
    }

    bool remove(int value) {
        if (!root) return false;

        if (root->value == value) {
            root.reset();
            return true;
        }

        return remove_node(root->children, value);
    }

    bool replace(int old_value, int new_value) {
        Node* node = find(root.get(), old_value);
        if (!node) return false;

        node->value = new_value;
        return true;
    }


    void print_tree() const {
        print_node(root.get(), 0);
    }
};




int main() {
    Tree tree(1);

    tree.add(1, 2);
    tree.add(1, 3);
    tree.add(2, 4);
    tree.add(2, 5);
    tree.insert(1, 99, 1);

    std::cout << "Initial tree:\n";
    tree.print_tree();

    tree.replace(4, 42);

    std::cout << "\nAfter replace:\n";
    tree.print_tree();

    tree.remove(2);

    std::cout << "\nAfter removing subtree rooted at 2:\n";
    tree.print_tree();
}

