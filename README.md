https://github.com/trrne/box

![](http://github-profile-summary-cards.vercel.app/api/cards/stats?username=cet-t&theme=dark)
![](http://github-profile-summary-cards.vercel.app/api/cards/stats?username=cet-t&theme=default)

```
set tabstop=4
set shiftwidth=4
set expandtab
set clipboard=unnamed

set number
" set guifont=DroidSansMono\ Nerd\ Font\ 13
" set guifontwide=DroidSansMono\ Nerd\ Font\ 13
set hlsearch
set smartindent
set laststatus=2
set wildmenu
set lines=70 columns=150
set ruler
set history=1000
set encoding=utf8
syntax enable

" KEY SETTINGS
" https://vimblog.hatenablog.com/entry/vimrc_key_mapping
nmap <ff> :NERDTreeToggle<CR>
" Shift Lで行末に移動
noremap L $
" Shift Hで行頭に移動
noremap H 0


" PLUGIN SETTINGS
call plug#begin('~/.config/nvim/plugged')

Plug 'vim-airline/vim-airline'
Plug 'vim-airline/vim-airline-themes'
Plug 'tpope/vim-commentary'
Plug 'neoclide/coc.nvim', {'branch': 'release'}
Plug 'preservim/nerdtree'
Plug 'ryanoasis/vim-devicons'

Plug 'SirVer/ultisnips'
Plug 'honza/vim-snippets'

call plug#end()

" NERDTree SETTINGS
autocmd VimEnter * execute 'NERDTree'
nmap <C-f> :NERDTreeToggle<CR>
let g:airline#extensions#tabline#enabled = 1
nmap <C-p> <Plug>AirlineSelectPrevTab
nmap <C-n> <Plug>AirlineSelectNextTab
" Airline SETTINGS
let g:airline_powerline_fonts = 1

hi VertSplit cterm=none

if exists('g:vscode')
" Neovim Ui Modifier SETTINGS
    function! SetCursorLineNrColorInsert(mode)
        " Insert mode: blue
        if a:mode == "i"
            call VSCodeNotify('nvim-theme.insert')

        " Replace mode: red
        elseif a:mode == "r"
            call VSCodeNotify('nvim-theme.replace')
        endif
    endfunction

    augroup CursorLineNrColorSwap
        autocmd!
        autocmd ModeChanged *:[vV\x16]* call VSCodeNotify('nvim-theme.visual')
        autocmd ModeChanged *:[R]* call VSCodeNotify('nvim-theme.replace')
        autocmd InsertEnter * call SetCursorLineNrColorInsert(v:insertmode)
        autocmd InsertLeave * call VSCodeNotify('nvim-theme.normal')
        autocmd CursorHold * call VSCodeNotify('nvim-theme.normal')
    augroup END
endif
```
