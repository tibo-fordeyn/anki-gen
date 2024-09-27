" Anki specific conceal for \akq and \akns
syntax match texAkq "\\akq" conceal cchar=?  
syntax match texAkns "\\akns" conceal cchar=! 

" Conceal begin and end LaTeX environments (thanks to reddit comment by dualfoothands)
call matchadd('Conceal', '\\begin{\ze[^}]\+}', 10, -1, {'conceal':'['})
call matchadd('Conceal', '\\begin{[^}]\+\zs}\ze', 10, -1, {'conceal':']'})

call matchadd('Conceal', '\\end\ze{[^}]\+}', 10, -1, {'conceal':'['})
call matchadd('Conceal', '\\end\zs{\ze[^}]\+}', 10, -1, {'conceal':'/'})
call matchadd('Conceal', '\\end{[^}]\+\zs}\ze', 10, -1, {'conceal':']'})


