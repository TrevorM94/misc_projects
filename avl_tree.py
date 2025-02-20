class Node:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None
        self.height = 1

class AVLTree:
    # Get the height of the node
    def get_height(self, node):
        if not node:
            return 0
        return node.height
    
    # Get the balance factor of the node
    def get_balance(self, node):
        if not node:
            return 0
        return self.get_height(node.left) - self.get_height(node.right)

    # Perform a right rotation
    def right_rotate(self, z):
        y = z.left
        T3 = y.right
        y.right = z
        z.left = T3

        z.height = 1 + max(self.get_height(z.left), self.get_height(z.right))
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))

        return y

    # Perform a left rotation
    def left_rotate(self, z):
        y = z.right
        T2 = y.left
        y.left = z
        z.right = T2

        z.height = 1 + max(self.get_height(z.left), self.get_height(z.right))
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))

        return y

    # Insert a node
    def insert(self, root, key):
        # Step 1: Perform the normal BST insertion
        if not root:
            return Node(key)
        elif key < root.key:
            root.left = self.insert(root.left, key)
        else:
            root.right = self.insert(root.right, key)

        # Step 2: Update the height of the ancestor node
        root.height = 1 + max(self.get_height(root.left), self.get_height(root.right))

        # Step 3: Get the balance factor
        balance = self.get_balance(root)

        # Step 4: Balance the node if unbalanced

        # Left Left Case
        if balance > 1 and key < root.left.key:
            return self.right_rotate(root)

        # Right Right Case
        if balance < -1 and key > root.right.key:
            return self.left_rotate(root)

        # Left Right Case
        if balance > 1 and key > root.left.key:
            root.left = self.left_rotate(root.left)
            return self.right_rotate(root)

        # Right Left Case
        if balance < -1 and key < root.right.key:
            root.right = self.right_rotate(root.right)
            return self.left_rotate(root)

        return root

    # Preorder traversal of the tree
    def pre_order(self, root):
        if not root:
            return
        print(f"{root.key} ", end="")
        self.pre_order(root.left)
        self.pre_order(root.right)

if __name__ == "__main__":
    avl_tree = AVLTree()
    root = None

    numbers = [10, 20, 30, 40, 50, 25]
    for number in numbers:
        root = avl_tree.insert(root, number)

    # Preorder Traversal
    print("Preorder traversal of the AVL tree is:")
    avl_tree.pre_order(root)
