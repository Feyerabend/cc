/*
 * BinarySearchTree.java
 *
 * A simple demonstration example made for
 * publication in DatorMagazin 2001.
 * Free to use.
 */
package demo.dmz;

/**
 * The <code>BinarySearchTree</code> class represents a tree of nodes.
 * Restrictions: It uses a special object for representing a nil value,
 * internally.
 *
 * @author  S. Lonnert
 * @version 0.01, 99
 */
public class BinarySearchTree {

 /**
  * The root.
  */
  protected TreeNode root;

 /**
  * The special end-nodes. Can be overridden in subclass.
  */
  protected static TreeNode nil = new TreeNode(0, "nil");

 /**
  * Check if tree is empty. Return true if it is empty, otherwise false.
  *
  * @return     true, if the tree is empty.
  */
  public boolean isEmpty() {
    return (root == null);
  }

 /**
  * Empty the tree.
  */
  public void setEmpty() {
    setEmptyNodes(root);
    root = null; // dangling ref?
  }

  private void setEmptyNodes(TreeNode x) {
    if (x != null) {
      setEmptyNodes(x.left);
      setEmptyNodes(x.right);
      x.key = 0;
      x.value = null;
      x = null;
    }
  }

 /**
  * Return root of tree.
  *
  * @return     root of tree.
  */
  public TreeNode getRoot() {
    return root;
  }

 /**
  * Returns the <em>minimum</em> TreeNode in the tree, given
  * a TreeNode (which can be the root). Here the <em>minimum</em> node
  * is represented as the leftmost node, as the tree is already
  * sorted. (Common property.)
  *
  * @param   x   the TreeNode used for departure.
  * @return  the minimum node in the tree.
  */
  public TreeNode minimum(TreeNode x) {
    while (x.left != null) {
      x = x.left;
    }
    return x;
  }

 /**
  * Returns the <em>maximum</em> TreeNode in the tree, given
  * a TreeNode (which can be the root). Here the <em>maximum</em> node
  * is represented as the rightmost node, as the tree is already
  * sorted. (Common property.)
  *
  * @param   x   the TreeNode used for departure.
  * @return  the maximum node in the tree.
  */
  public TreeNode maximum(TreeNode x) {
    while (x.right != null) {
      x = x.right;
    }
    return x;
  }

 /**
  * Returns the <em>successor</em> TreeNode in the tree.
  * (Common property.)
  *
  * @param   x   the TreeNode used for departure.
  * @return  the sucessor node in the tree.
  * @see #minimum
  */
  public TreeNode successor(TreeNode x) {
    if (x.right != null) {
      return minimum(x.right);
    }
    TreeNode y = x.parent;
    while ((y != null) && (x == y.right)) {
      x = y;
      y = x.parent; // alt: y.parent :)
    }
    return y;
  }

 /**
  * Returns the <em>predecessor</em> TreeNode in the tree.
  * (Common property.)
  *
  * @param   x   the TreeNode used for departure.
  * @return  the predecessor node in the tree.
  * @see #maximum
  */
  public TreeNode predecessor(TreeNode x) {
    if (x.left != null) {
      return maximum(x.left);
    }
    TreeNode y = x.parent;
    while ((y != null) && (x == y.left)) {
      x = y;
      y = x.parent; // alt: y.parent :)
    }
    return y;
  }

 /**
  * Inserts a TreeNode in the tree (starting from the root). The TreeNode
  * has to be given a unique key, if not to replace a matching key of a
  * already stored TreeNode in the tree.
  * If the result is null, there has <strong>not</strong> been a match and
  * the TreeNode has been inserted. Otherwise, a replacement has been done,
  * with the returning TreeNode replaced.
  *
  * @param   z   the TreeNode used for departure.
  * @return  null if the inserted TreeNode has a unique key;
  *          otherwise returns the replaced TreeNode if the keys match.
  */
  public TreeNode insert(TreeNode z) {
    TreeNode x = root, y = null;
    while (x != null) {
      y = x;
      if (z.key < x.key) {
        x = x.left;
      } else {
        x = x.right;
      }
    }
    z.parent = y;
    if (y == null) {
      root = z;
    } else {
      if (z.key < y.key) {
        y.left = z;
      } else if (z.key > y.key) {
        y.right = z;
      } else {
        // swap
        Object t = z.value;
        z.value = y.value;
        y.value = t;
        return z;
      }
    }
    return null;
  }

 /**
  * Deletes a TreeNode in the tree (starting from the root).
  *
  * @param   z   the TreeNode to delete.
  * @return  deleted node. (Future: collect NILs.)
  * @see #successor
  */
  public TreeNode delete(TreeNode z) {
    TreeNode x = null, y = null;
    if ((z.left == null) || (z.right == null)) {
      y = z;
    } else {
      y = successor(z);
    }
    if (y.left != null) {
      x = y.left;
    } else {
      if (y.right == null) {
        x = nil;
      } else {
        x = y.right;
      }
    }
    if (x != null) {
      x.parent = y.parent;
    }
    if (y.parent == null) {
      if (x == nil) {
        root = null;
      } else {
        root = x;
      }
    } else {
      if (y == y.parent.left) {
        if (x == nil) {
          y.parent.left = null;
        } else {
          y.parent.left = x;
        }
      } else {
        if (x == nil) {
          y.parent.right = null;
        } else {
          y.parent.right = x;
        }
      }
    }
    if (y != z) {
      z.key = y.key;
      z.value = y.value; // if more fields: copy them!
    }
    return y;
  }

 /**
  * Erases a TreeNode in the tree, given a key.
  *
  * @param   k   the key for the searched node.
  * @return  the erased node.
  * @see #delete
  * @see #search
  * @see #getRoot
  * @throws  EmptyTreeException  if there is no matching key/node to erase
  */
  public TreeNode erase(int k)
  throws EmptyTreeException {
    TreeNode z = search(getRoot(), k);
    if (z != null) {
      return delete(z);
    }
    throw new EmptyTreeException();
  }

 /**
  * Prints the tree with the key and corresponding value
  * in an inorder walk.
  *
  * @param   x   the TreeNode used for departure (usually the root).
  */
  public void inorderWalk(TreeNode x) {
    if (x != null) {
      inorderWalk(x.left);
      System.out.println(" For key: " + x.key + ", value: " + x.value);
      inorderWalk(x.right);
    }
  }

 /**
  * Returns the value of a stored object in the tree, given a key.
  *
  * @param   x   the TreeNode used for departure (usually the root).
  * @param   k   the integer key.
  * @return  the node corresponding to the key; if not found, it will return value
  *          null indicates that the object is not in the tree.
  */
  public TreeNode search(TreeNode x, int k) {
    if ((x == null) || (k == x.key)) {
      return x;
    }
    if (k < x.key) {
      return search(x.left, k);
    } else {
      return search(x.right, k);
    }
  }
}

