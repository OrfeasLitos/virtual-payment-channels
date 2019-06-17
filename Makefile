all: virtualChannels.pdf

#.ONESHELL:
virtualChannels.pdf: src/*
	export TEXINPUTS=.:./src//:; \
	pdflatex virtualChannels.tex; \
	rm -rf virtualChannels.aux virtualChannels.log virtualChannels.out virtualChannels.toc virtualChannels.lof virtualChannels.lot virtualChannels.bbl virtualChannels.blg

bib: src/*
	export TEXINPUTS=.:./src//:; \
	pdflatex virtualChannels.tex; \
	bibtex virtualChannels.aux; \
	pdflatex virtualChannels.tex; \
	pdflatex virtualChannels.tex; \
	rm -rf virtualChannels.aux virtualChannels.log virtualChannels.out virtualChannels.toc virtualChannels.lof virtualChannels.lot virtualChannels.bbl virtualChannels.blg

clean:
	rm -rf *.aux *.log *.out *.toc *.lof *.lot *.bbl *.blg *.pdf
