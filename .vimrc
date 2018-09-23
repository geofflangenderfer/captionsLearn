
" An example for a vimrc file.
"
" Maintainer:	Bram Moolenaar <Bram@vim.org>
" Last change:	2017 Sep 20
"
" To use it, copy it to
"     for Unix and OS/2:  ~/.vimrc
"	      for Amiga:  s:.vimrc
"  for MS-DOS and Win32:  $VIM\_vimrc
"	    for OpenVMS:  sys$login:.vimrc

" When started as "evim", evim.vim will already have done these settings.
if v:progname =~? "evim"
  finish
endif

" Get the defaults that most users want.
source $VIMRUNTIME/defaults.vim

if has("vms")
  set nobackup		" do not keep a backup file, use versions instead
else
  set backup		" keep a backup file (restore to previous version)
  if has('persistent_undo')
    set undofile	" keep an undo file (undo changes after closing)
  endif
endif

if &t_Co > 2 || has("gui_running")
  " Switch on highlighting the last used search pattern.
  set hlsearch
endif

" Only do this part when compiled with support for autocommands.
if has("autocmd")

  " Put these in an autocmd group, so that we can delete them easily.
  augroup vimrcEx
  au!

  " For all text files set 'textwidth' to 78 characters.
  autocmd FileType text setlocal textwidth=78

  augroup END

else

  set autoindent		" always set autoindenting on

endif " has("autocmd")

" Add optional packages.
"
" The matchit plugin makes the % command work better, but it is not backwards
" compatible.
" The ! means the package won't be loaded right away but when plugins are
" loaded during initialization.
if has('syntax') && has('eval')
  packadd! matchit
endif

" map copy/cut to usual functionality
" map paste (insert mode) to normal
vnoremap <C-c> "+y
inoremap <C-v> <C-o>"+p
vnoremap <C-d> "+d

" use spaces instad of tabs
set tabstop=4
set softtabstop=4
set shiftwidth=4
set shiftround
set expandtab

" show line numbers and length
set number " show line numbers
set tw=79  " width of document (used by gd)
set nowrap " don't automatically wrap on load
set fo-=t  " don't automatically wrap text when typing
set colorcolumn=80
highlight ColorColumn ctermbg=233


" syntax on
filetype off
filetype plugin indent on
syntax on

" set colorscheme to hemisu, which should be good for light/dark screens
colorscheme hemisu

" better copy/paste
set pastetoggle=<F2>
set clipboard=unnamed

" rebind <Leader> key
let mapleader = ","

" nohl bind
noremap <C-n> :nohl<CR>
vnoremap <C-n> :nohl<CR>
inoremap <C-n> :nohl<CR>

" quick save command
noremap <C-P> :update<CR>
vnoremap <C-P> :update<CR>
inoremap <C-P> :update<CR>

" bind Ctrol+<movement> keys to move around windows instaed of
" Ctrl+w+<movement>
map <c-h> <c-w>h
map <c-j> <c-w>j
map <c-k> <c-w>k
map <c-l> <c-w>l

" easier moving between tabs
map <Leader>n <esc>:tabprevious<CR>
map <Leader>m <esc>:tabnext<CR>

" map sort function 
vnoremap <Leaders>s :sort<CR>

" move code blocks easier
vnoremap < <gv 
vnoremap > > gv 

" show whitespace
" MUST be inserted BEFORE the colorscheme command 
autocmd ColorScheme * highlight ExtraWhitespace ctermbg=red guibg=red
au InsertLeave * match ExtraWhitespace /\s\+$/

" Color scheme
" mkdir -p ~/.vim/colors && cd ~/.vim/colors
" wget -O wombat256mod.vim http://www.vim.org/scripts/download_script.php?s
set t_Co=256
color wombat256mod

" collect all backup ~ files in one place 
set undodir=/home/geoff/.vim_undo

" turn on case-insensitive search
set hlsearch
set incsearch
set ignorecase
set smartcase

" disable ~ and .swp files
"" set nobackup
"" set nowritebackup
"" set noswapfile

" setup Pathogen to handle plugins 
" mkdir -p ~/.vim/autoload ~/.vim/bundle
" curl -so ~/.vim/autoload/pathogen.vim https://github.com/tpope/vim-pathogen.git
" Now you can install any plugin into a .vim/blundle/plugin_name/ folder
call pathogen#infect()



" =========================================================================
" Python IDE Setup
" =========================================================================

" settings for vim-powerline
" cd ~/.vim/bundle
" https://github.com/powerline/powerline.git
set laststatus=2

" settings for ctrlp
" cd ~/.vim/bundle
" https://github.com/kien/ctrlp.vim.git
let g:ctrlp_max_height= 30
set wildignore+=*.pyc
set wildignore+=*_build/*
set wildignore+=*/coverage/*

" settings for python-mode
" cd ~/.vim/bundle
" git clone https://github.com/python-mode/python-mode.git
map <Leader>g :call RopeGotoDefinition()<CR>
let ropevim_enable_shortcuts = 1
let g:pymode_rope_goto_def_newwin = "vnew"
let g:pymode_rope_extended_complete = 1
let g:pymode_breakpoint = 0
let g:pymode_syntax = 1
let g:pymode_syntax_builtin_objs = 0
let g:pymode_syntax_builtin_funcs = 0
map <Leader>b Oimport ipdb; ipdb.set_trace() # BREAKPOINT<C-c>

" Settings for jedi-vim: autocomplete, docs
" cd ~/.vim/bundle
"  git clone --recursive https://github.com/davidhalter/jedi-vim.git ~/.vim/bundle/jedi-vim
let g:jedi#usages_command = "<leader>z"
let g:jedi#popup_on_dot = 0
let g:jedi#popup_select_first = 0
map <Leader>b Oimport ipdb; ipdb.set_trace() # BREAKPOINT<C-c>

" Better navigating through omnicomplete option list
" See http://stackoverflow.com/questions/2170023/how-to-map-keys-for-popup-menu-in-vim
set completeopt=longest,menuone
function! OmniPopup(action)
    if pumvisible()
        if a:action == 'j'
            return "\<C-N>"
        elseif a:action == 'k'
            return "\<C-P>"
        endif
    endif
    return a:action
endfunction

 inoremap <silent><C-j> <C-R>=OmniPopup('j')<CR>
 inoremap <silent><C-k> <C-R>=OmniPopup('k')<CR>

" Python folding
" mkdir -p ~/.vim/ftplugin
" wget -O ~/.vim/ftplugin/python_editing.vim
" www.vim.org/scripts/download_script.php?src_id=5492
" f folds a single block
" F folds all code
set nofoldenable



" pair program easy with wemux
"https://github.com/zolrath/wemux
