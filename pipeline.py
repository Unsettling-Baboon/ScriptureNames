import math as m, text_retriever, names_extractor

def get_names_from_chapter(canto: int, chapter: int):
    # retrieve the relevant texts and initialize limits

    source_ref = f"Srimad Bhagavatam, Canto {canto}, Chapter {chapter}"
    exclude_names_file = f'sb_canto{canto}_chapter{chapter}_names.json'
    texts = text_retriever.get_texts_from_chapter(canto, chapter)
    curr_iter, max_iter = 0, m.ceil(len(texts) / 20)
    
    # payload concatenation

    while curr_iter < max_iter:
        # refresh the step size

        start_index = 20 * curr_iter
        step = min(20, len(texts) - start_index)

        # feed into name extractor

        source_str = ' '.join(texts[start_index:start_index + step])
        found_names = names_extractor.extract_names(source_str, source_ref, exclude_names_file)

        # extract names to JSON file

        names_extractor.extract_names_to_json(canto, chapter, found_names)

        # advance iter

        curr_iter += 1

def get_names_from_sb():
    canto, chapter = 1, 1
    while canto <= 12:
        try:
            get_names_from_chapter(canto, chapter)
            chapter += 1
        except ValueError:
            canto, chapter = canto + 1, 1

get_names_from_chapter(5, 2)