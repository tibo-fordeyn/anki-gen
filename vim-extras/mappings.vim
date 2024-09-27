" Anki mappings!
nnoremap <leader>aa :call system('~/.local/share/anki-gen/scripts/aa.py ' . shellescape(expand('%')))<CR>
nnoremap <leader>as :call system('~/.local/share/anki-gen/scripts/as.py ' . shellescape(expand('%')))<CR>
nnoremap <leader>ad :call system('~/.local/share/anki-gen/scripts/ad.py ' . shellescape(expand('%')))<CR>
nnoremap <leader>ae :call system('~/.local/share/anki-gen/scripts/ae.py ' . shellescape(expand('%')))<CR>
" By making the remaps this way, you won't have to "enter", do or see anything
" after executing. Just the way I like it.

" Function to surround selected text with Anki commands
function! SurroundWithAnki(command)
    let first_line = line("'<")
    let last_line = line("'>")
    " Insert command at the end of the line before the first selected line
    if first_line > 1
        let before_line = first_line - 1
        let prev_line = getline(before_line)
        call setline(before_line, prev_line . '\' . a:command . '{')
    else
        " If at the first line, insert at the beginning
        let curr_line = getline(first_line)
        call setline(first_line, '\' . a:command . '{' . curr_line)
    endif
    " Insert closing brace at the beginning of the line after the last selected line
    if last_line < line('$')
        let after_line = last_line + 1
        let next_line = getline(after_line)
        call setline(after_line, '}' . next_line)
    else
        " If at the last line, append a new line with '}'
        call append(line('$'), '}')
    endif
endfunction

" Mappings for Anki commands in visual mode
vnoremap <leader>q :<C-U>call SurroundWithAnki('akq')<CR>
vnoremap <leader>a :<C-U>call SurroundWithAnki('akns')<CR>

" Function to delete Anki commands around selected text
function! DeleteAnkiWrapper() range
    let first_line = a:firstline
    let last_line = a:lastline
    let removed = 0
    " Check if line before the first selected line contains \akq{ or \akns{
    if first_line > 1
        let before_line_num = first_line - 1
        let before_line = getline(before_line_num)
        if before_line =~ '\\\(akq\|akns\){$'
            " Remove \akq{ or \akns{ from the end of the line
            let new_before_line = substitute(before_line, '\\\(akq\|akns\){$', '', '')
            call setline(before_line_num, new_before_line)
            let removed += 1
        endif
    endif
    " Check if line after the last selected line contains a closing }
    if last_line < line('$')
        let after_line_num = last_line + 1
        let after_line = getline(after_line_num)
        if after_line =~ '^}'
            " Remove the } from the beginning of the line
            let new_after_line = substitute(after_line, '^}', '', '')
            call setline(after_line_num, new_after_line)
            let removed += 1
        endif
    endif
    if removed == 0
        echo "No Anki wrapper found around selection."
    endif
endfunction
"  Mapping to delete Anki wrapper in visual mode
vnoremap <leader>d :<C-U>call DeleteAnkiWrapper()<CR>

