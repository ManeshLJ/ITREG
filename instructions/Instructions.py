import pypandoc

# Export zu HTML
pypandoc.convert_file("Anleitung.md", "html", outputfile="Anleitung.html", extra_args=["--include-in-header=header.html"])

# Export zu PDF
pypandoc.convert_file("Anleitung.md", "pdf", outputfile="Anleitung.pdf")