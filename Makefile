all: virtualChannels.pdf

#.ONESHELL:
virtualChannels.pdf: src/*
	export TEXINPUTS=.:./src//:; \
	pdflatex --shell-escape virtualChannels.tex; \
	rm -rf virtualChannels.aux virtualChannels.log virtualChannels.out virtualChannels.toc virtualChannels.lof virtualChannels.lot virtualChannels.bbl virtualChannels.blg virtualChannels-autopp.out virtualChannels-pics.pdf

bib: src/*
	export TEXINPUTS=.:./src//:; \
	pdflatex --shell-escape virtualChannels.tex; \
	bibtex virtualChannels.aux; \
	pdflatex --shell-escape virtualChannels.tex; \
	pdflatex --shell-escape virtualChannels.tex; \
	rm -rf virtualChannels.aux virtualChannels.log virtualChannels.out virtualChannels.toc virtualChannels.lof virtualChannels.lot virtualChannels.bbl virtualChannels.blg virtualChannels-autopp.out virtualChannels-pics.pdf

clean:
	rm -rf *.aux *.log *.out *.toc *.lof *.lot *.bbl *.blg *.pdf
