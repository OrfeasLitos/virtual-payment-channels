all: virtual-channels.pdf

#.ONESHELL:
virtual-channels.pdf: src/*
	export TEXINPUTS=.:./src//:; \
	pdflatex --shell-escape virtual-channels.tex; \
	rm -rf virtual-channels.aux virtual-channels.log virtual-channels.out virtual-channels.toc virtual-channels.lof virtual-channels.lot virtual-channels.bbl virtual-channels.blg virtual-channels-autopp.out virtual-channels-pics.pdf virtual-channels-autopp.log

bib: src/*
	export TEXINPUTS=.:./src//:; \
	pdflatex --shell-escape virtual-channels.tex; \
	bibtex virtual-channels.aux; \
	pdflatex --shell-escape virtual-channels.tex; \
	pdflatex --shell-escape virtual-channels.tex; \
	rm -rf virtual-channels.aux virtual-channels.log virtual-channels.out virtual-channels.toc virtual-channels.lof virtual-channels.lot virtual-channels.bbl virtual-channels.blg virtual-channels-autopp.out virtual-channels-pics.pdf virtual-channels-autopp.log

clean:
	rm -rf *.aux *.log *.out *.toc *.lof *.lot *.bbl *.blg *.pdf
