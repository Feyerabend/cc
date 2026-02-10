/*
 * BinarySearchTreeTest.java
 *
 * A simple demonstration example made for
 * publication in DatorMagazin 2001.
 */
package demo.dmz.test;

import demo.dmz.BinarySearchTree;
import demo.dmz.TreeNode;
import demo.dmz.EmptyTreeException;

import junit.framework.Test;
import junit.framework.TestCase;
import junit.framework.TestSuite;


public class BinarySearchTreeTest extends TestCase {

  private BinarySearchTree b;
  private TreeNode s;

 /**
  * A <code>BinarySearchTreeTest</code> with
  * specified name.
  *
  * @param name   test case name.
  */
  public BinarySearchTreeTest(String name) {
    super(name);
  }

 /**
  * Setup for test. Defined in JUnit.
  * Called before every test case method.
  */
  protected void setUp() {
    b = new BinarySearchTree();
    s = new TreeNode(6, "Macaper");

    b.insert(new TreeNode(10, "Hyperbolis"));
    b.insert(new TreeNode(2, "Margolia"));
    b.insert(s);
    b.insert(new TreeNode(8, "Hyperbolis"));
    b.insert(new TreeNode(12, "Moree"));
    b.insert(new TreeNode(4, "Grounded"));
  }

 /**
  * Teardown for test. Defined in JUnit.
  * Called after every test case method (clean up).
  */
  protected void tearDown() {
    b.setEmpty();
    b = null;
  }

 /**
  * Tests emptiness.
  */
  public void testEmpty() {
    b.setEmpty();
    assert(b.isEmpty());
  }

 /**
  * Tests emptiness, by deleting from empty tree.
  */
  public void testDeleteFromEmpty() {
    b.setEmpty();
    b.delete(new TreeNode(10, "Hipp"));
    assert(b.isEmpty());
  }

 /**
  * Tests delete, by retrieving a replacement,
  * and check for equality.
  */
  public void testDeleteExampleS() {
    TreeNode t = new TreeNode(6, "Macaper");
    assertEquals(b.delete(t), s);
  }

 /**
  * Tests erasing, with no exception.
  */
  public void testEmptyTree() {
    try {
      TreeNode t = new TreeNode(6, "Macaper");
      b.erase(6);
    } catch (EmptyTreeException e) { }
  }

 /**
  * Tests erasing, throwing an exception.
  */
  public void testEmptyTreeException() {
    try {
      b.erase(17); // non-existent
    } catch (EmptyTreeException e) {
      return;
    }
    fail("Should raise EmptyTreeException");
  }

 /**
  * Tests node equality.
  */
  public void testEqual() {
    TreeNode t = new TreeNode(6, "Macaper");
    assertEquals(t, s);
    assert(t.equals(s));
  }

 /**
  * Tests tree-values by searching for a given node, retieving
  * its value and compare.
  */
  public void testEqualValues() {
    assertEquals("Moree", b.search(b.getRoot(), 12).getValue());
  }

 /**
  * Tests replacement, by replaing a node through the equality of keys
  * and comparing results of values.
  */
  public void testReplacement() {
    TreeNode t = new TreeNode(4, "Poff!");
    b.insert(t);
    assertEquals("Poff!", b.search(b.getRoot(), 4).getValue());
  }


 /**
  * Returns a test suite for
  * all test methods.
  *
  * @return Test suite.
  */
  public static Test suite() {
    TestSuite suite =
      new TestSuite(BinarySearchTreeTest.class);
    return suite;
  }

 /**
  * String representation of this
  * test returned.
  *
  * @return Test case name.
  */
  public String toString() {
    return name();
  }

  // main
  public static void main(String args[]) {
    String[] testCaseName = {
      BinarySearchTreeTest.class.getName()
    };
    junit.textui.TestRunner.main(testCaseName); // alt. text
    //junit.swingui.TestRunner.main(testCaseName); // alt. swing
    //junit.ui.TestRunner.main(testCaseName); // alt. awt
  }
}
