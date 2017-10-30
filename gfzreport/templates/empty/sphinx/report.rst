.. Empty report template. Please fill your custom text here below.
   This is a RsT (ReStructuredText) file and also a comprehensive tutorial
   which might help you during editing. RsT is a lightweight markup language designed to be both
   easily readable/editable and processable by documentation-processing software (sphinx) to
   produce html, latex or pdf output


.. this is the abstract (AUTHOR INPUT) and will be rendered in latex within the 
   abstract environment (\begin{abstract} ... \end{abstract}):

:abstract: write your abstract here, you can add newlines but remeber:
           you should indent
           any new line

.. ==============================================================================   


..  RST syntax help
    ===============
    
    (delete this section when no longer needed / after completion of editing)
    
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    .. TEXT FORMATTING:
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    This is an example of "normal" body text. It's not in a comment block.
    Remeber that indentation is a special RsT command and that newlines are actually not rendered
    (this is a newline and you shouldn't see any difference in html or latex)
    
    But you can type a new paragraph by adding an empty line above it (like in
    this case)
    
    .. italic can be rendered by wrapping text within two asterix, bold by wrapping
       text within two couples of asterix:
       
    *This is rendered in italic*, **this is rendered in bold**
    
    
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    .. HYPERLINKS:
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    .. Hyperlink (inline): simply type them: Urls are automatically recognized and linked:
    
    Hyperlink (inline): http://www.python.org/
    
    .. Hyperlink with substitution text: point to the same url as above but render 'Python' as text:
    
    Hyperlink with subsitution text: `Python <http://www.python.org/>`_
    
    .. Hyperlink with substitution text, if it has to be referenced more than once.
       Define the hyperlink as follows (note that the line below is NOT rendered but is NOT a comment):
       
    .. _Wikipedia: https://www.wikipedia.org/
    
    Hyperlinks with subsitution text referenced more than once: Wikipedia_, and again, Wikipedia_ 
    
    
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    .. TEXT SUBSTITUTIONS:
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    .. When the a text is repeated many times throughout one or more documents,
       especially if it may need to change later
       (note that the line below is NOT rendered but is NOT a comment):
    
    .. |RsT| replace:: ReStructuredText
    
    Text substitution: |RsT|
    
    .. Note that by placing a backslash before a character, you render that character
       literally. E.g., concerning the text substitution just descirbed:
    
    |RsT| was obtained by typing \|RsT\|
    
    
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    .. MATH FORMULAE:
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    .. Inline math formulae, use :math:`...` or latext dollar sign with latex syntax inside
       (the latter is not standard rst, but is implemented in this report):
    
    Here an inline math expression: :math:`(\alpha > \beta)` = $(\alpha > \beta)$
    
    .. More complex math formulae, use ..math:: then new empty line and INDENTED text:
    
    Here a more complex math expression:
    
    .. math::
    
       n_{\mathrm{offset}} = \sum_{k=0}^{N-1} s_k n_k
    
    
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    .. FOOTNOTES:
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    .. Footnotes with manual numbering:
    
    .. [1] First footnote
    
    .. [2] Second footnote, note that
       newlines which must be indented
    
    Here a ref to the first footnote [1]_ and here to the second [2]_.
    
    .. Footnotes with auto numbering (newlines must be INDENTED of at least three spaces):
    
    .. [#] First footnote (autonumbered)
    
    .. [#] Second footnote (autonumbered), note that
       newlines which must be indented
    
    Here a ref to the first footnote [#]_ and here to the second [#]_.
    
    .. Footnotes with auto numbering, referenced more than once (newlines must be INDENTED of at least three spaces):
    
    .. [#firstnote] First footnote (autonumbered, referenced more than once)
    
    .. [#secondnote] Second footnote (autonumbered, referenced more than once), note that
       newlines which must be indented
    
    Here a ref to the first footnote [#firstnote]_, again [#firstnote]_ and here to the second [#secondnote]_.
    
    .. Footnotes with auto symbols. DEPRECATED: seems they are buggy in latex:
    
    .. [*] First footnote (autosymbol)
    
    .. [*] Second footnote (autosymbol), note that
       newlines which must be indented
    
    Here a ref to the first footnote [*]_, and here to the second [*]_.
    
    
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    .. CITATIONS:
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    .. Citations are identical to footnotes except that their labels
       must be case-insensitive single words of alphanumerics plus internal hyphens,
       underscores, and periods. No whitespace, no numeric only. E.g., CIT2002:
    
    .. [CIT2002] Deep India meets deep Asia: Lithospheric indentation, delamination and break-off under
       Pamir and Hindu Kush (Central Asia). http://doi.org/10.1016/j.epsl.2015.11.046
    
    Here a reference to a publication: [CIT2002]_. And here another reference to it ([CIT2002]_)
    
    
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    .. NUMERIC REFERENCES TO FIGURES AND TABLES:
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    .. Providing a label to a specific directive (e.g. figure, table, see below):
       .. _labelname
       you can reference it in the text with:
       :numref:`labelname`
       
       For instance, here you can reference the auto-generated figures and tables
       (more on this below, if you are interested)
    
    Here a reference to :numref:`stations_table`. Here a reference to :numref:`stations_figure`.
    Here a reference to :numref:`inst_uptimes_figure`. Here a reference to :numref:`noise_pdfs_figure`
       
    
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    .. LIST ITEMS:
    .. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    .. bullet lists (blank line before and after the list):
    
    - This is a bullet list.
    
    - Bullets can be "*", "+", or "-".
    
    .. enumerated lists (blank line before and after the list):
    
    1. This is an enumerated list.
    
    2. Enumerators may be arabic numbers, letters, or roman
       numerals.
       
    .. nested lists (blank lines are optional between items on the same level):
    
    * About RsT syntax:
    
      - https://pythonhosted.org/an_example_pypi`_project/sphinx.html#restructured-text-rest-resources
        (and links therein)
      - http://docutils.sourceforge.net/docs/user/rst/quickref.html
     
    * About Sphinx syntax (RsT with some commands added)
    
      - http://www.sphinx-doc.org/en/stable/rest.html#rst-primer
        
    **More detailed tutorials**:
    
    - About RsT syntax:
      
      + http://docutils.sourceforge.net/rst.html 
        
    - About Sphinx:
      
      + http://www.sphinx-doc.org/en/stable/markup/index.html#sphinxmarkup
