TIKZS = $(patsubst src/figures/dot/%.dot, src/figures/auto-tikz/%.tex, $(wildcard src/figures/dot/*.dot))

all: figures virtual-channels.pdf

#.ONESHELL:
virtual-channels.pdf: src/* src/figures/auto-tikz/* src/figures/manual-tikz/*
	export TEXINPUTS=.:./src//:; \
	pdflatex --shell-escape -halt-on-error -interaction=nonstopmode virtual-channels.tex; \
	rm -rf virtual-channels.aux virtual-channels.log virtual-channels.out virtual-channels.toc virtual-channels.lof virtual-channels.lot virtual-channels.bbl virtual-channels.blg virtual-channels-autopp.out virtual-channels-pics.pdf virtual-channels-autopp.log virtual-channels-autopp.xcp

transactions-overview.pdf: src/transactions-overview/* src/transactions.tex
	export TEXINPUTS=.:./src//:; \
	pdflatex --shell-escape -halt-on-error -interaction=nonstopmode transactions-overview.tex; \
	bibtex transactions-overview.aux; \
	pdflatex --shell-escape -halt-on-error -interaction=nonstopmode transactions-overview.tex; \
	pdflatex --shell-escape -halt-on-error -interaction=nonstopmode transactions-overview.tex; \
	rm -rf transactions-overview.aux transactions-overview.log transactions-overview.out transactions-overview.toc transactions-overview.lof transactions-overview.lot transactions-overview.bbl transactions-overview.blg transactions-overview-autopp.out transactions-overview-pics.pdf transactions-overview-autopp.log

bib: figures src/*
	export TEXINPUTS=.:./src//:; \
	pdflatex --shell-escape -halt-on-error -interaction=nonstopmode virtual-channels.tex; \
	bibtex virtual-channels.aux; \
	pdflatex --shell-escape -halt-on-error -interaction=nonstopmode virtual-channels.tex; \
	pdflatex --shell-escape -halt-on-error -interaction=nonstopmode virtual-channels.tex; \
	rm -rf virtual-channels.aux virtual-channels.log virtual-channels.out virtual-channels.toc virtual-channels.lof virtual-channels.lot virtual-channels.bbl virtual-channels.blg virtual-channels-autopp.out virtual-channels-pics.pdf virtual-channels-autopp.log virtual-channels-autopp.xcp

figures: $(TIKZS)

src/figures/manual-tikz/*:

src/figures/auto-tikz/%.tex: src/figures/dot/%.dot
ifeq (, $(shell which dot2tex))
	
else
	mkdir -p src/figures/auto-tikz/
	dot2tex --texmode math --format tikz --figonly --autosize --usepdflatex --nominsize --prog dot $< > $@
endif

clean:
	rm -rf *.aux *.log *.out *.toc *.lof *.lot *.bbl *.blg *.pdf src/figures/auto-tikz/*.tex
