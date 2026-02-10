/*
 * TreeNode.java
 *
 * A simple demonstration example made for
 * publication in DatorMagazin 2001.
 * Free to use.
 */
package demo.dmz;

/**
 * The abstract <code>Node</code> class represents a node of
 * a tree, in general. It may thus be put somewhere else in
 * the future. It will then be made public.
 *
 * @author  S. Lonnert
 * @version 0.01, 99
 */
abstract class Node { }

/**
 * The <code>Node</code> class represents a node of
 * a tree. It may be changed in the future.
 *
 * @author  S. Lonnert
 * @version 0.01, 99
 */
public class TreeNode extends Node {

  // allow package restrictions
  // apply for simpler algoritms
  // in the same package

  Object value;
  int key;
  TreeNode left, right, parent;

 /**
  * Constructs a TreeNode with a key and its value.
  *
  * @param _key     A unique integer key (no duplicates allowed).
  * @param _value   A value corresponing to the key.
  */
  public TreeNode(int _key, Object _value) {
    key = _key;
    value = _value;
  }

 /**
  * The value in the node.
  *
  * @return     object.
  */
  public Object getValue() {
    return value;
  }

 /**
  * The integer key returned.
  *
  * @return     integer key.
  */
  public int getKey() {
    return key;
  }

 /**
  * Two arbitrary TreeNodes are equal, property.
  *
  * @return     true, if equal.
  */
  public boolean equals(Object o) {
    if (!(o instanceof TreeNode)) {
      return false;
    }
    TreeNode p = (TreeNode) o;
    return ((p.key == key) && p.value.equals(value));
  }
}
