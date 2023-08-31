(maphash 
 (lambda (key val)
   (princ (format "%c : %s\n" val key)))
 (ucs-names))
