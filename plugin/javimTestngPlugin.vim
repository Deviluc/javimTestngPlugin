if !has('python')
    echo "Error: Required vim compiled with +python"
    finish
endif

" --------------------------------
" Add javimTestngPlugin to the path
" --------------------------------
python3 import sys
python3 import vim
python3 sys.path.append(vim.eval('expand("<sfile>:h")'))
python3 from javimTestngPlugin import TestNGTestRunConfiguration

