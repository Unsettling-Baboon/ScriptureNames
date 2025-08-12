import sqlite3, json, re

def list_all_sb_chapters() -> list[tuple[str, str, int, int]]:
    """List all chapters from SB in the format (canto, 
    chapter, record_id) from the file named
    "gargamuni vedabase date.ivd" file (which is a sqlite
    file), and save it in a file
    
    Returns:
        A list of tuples containing the title of the canto, the
        title of the chapter, the record of the chapter's
        first text, and the record of the chapter's last text.
    """

    # connect to the SQLite database

    garg = sqlite3.connect('gargamuni vedabase data.ivd')
    cursor = garg.cursor()

    # execute the query to get all chapters

    cursor.execute(
        "SELECT parent.title, child.title, child.record as " \
        "first_text, child.next_sibling as last_text FROM contents " \
        "AS child JOIN contents AS parent ON child.parent = parent.record " \
        "WHERE child.level = 6 AND ( child.title LIKE 'SB _._:%' OR " \
        "child.title LIKE 'SB _.__:%' OR child.title LIKE 'SB __._:%' OR " \
        "child.title LIKE 'SB __.__:%' )"
        )
    
    # fetch all results

    chapters = cursor.fetchall()

    # print chapter results

    print(f"Found {len(chapters)} chapters in SB.")
    print("Chapters saved to sb_chapters.json.")

    # close the connection

    garg.close()

    # save the results to a JSON file

    with open('sb_chapters.json', 'w') as f:
        json.dump(chapters, f, indent=4)

    # return the list of chapters

    return chapters

def get_texts_from_chapter(canto: int, chapter: int) -> list[str]:
    """
    Given a canto and chapter from SB, retrieve the full text for each 
    text in a list, converting the text data into plain text without the 
    stylistic elements, for example: [“Text 1.1.1 …”, “Text 1.1.2 ….”, …]

    Uses the list_all_sb_chapters function to retrieve the chapter location
    and then retrieves the texts from the database, using the record from
    the next_sibling field to determine the end of the chapter.

    Args:
        canto (str): The canto number.
        chapter (str): The chapter number.
    Returns:
        All the content pertaining to the specified chapter.
    Raises:
        ValueError: If the canto or chapter is not found.
    """

    # format the canto and chapter into a string

    canto_chapter = f"SB {canto}.{chapter}:"

    # retrieve the chapters and save it in a variable

    chapters = list_all_sb_chapters()

    # find the chapter, and its relevant texts, concatenated

    for chapter_set in chapters:
        if canto_chapter in chapter_set[1]:
            # find the records for the first and last text of the chapter

            first_text_record, last_text_record = chapter_set[2], chapter_set[3]

            # initialize the connection to the database

            garg = sqlite3.connect('gargamuni vedabase data.ivd')
            cursor = garg.cursor()

            # find the texts

            cursor.execute(
                f"SELECT plain FROM texts WHERE recid >= {first_text_record} " \
                f"AND recid <= {last_text_record} " \
                )
            unformatted_texts = cursor.fetchall()
            
            '''
            format the texts by removing all text that is in BETWEEN
            brackets "<" and ">", in general
            '''

            formatted_texts = []
            for text in unformatted_texts:
                # remove the text between < and >
                formatted_text = re.sub(r'<.*?>', ' ', text[0])
                # add the formatted text to the list
                formatted_texts.append(formatted_text)

            '''
            next, proceed to concatenate the texts into a single string,
            then split it into pieces wherever they start with the string
            "TEXT (number)" or "TEXTS (number - number)", making sure that 
            each split piece still starts with the relevant "TEXT " or 
            "TEXTS " string, and that the split pieces are not empty
            '''
            
            # concatenate the formatted texts into a single string

            concatenated_text = ' '.join(formatted_texts)

            # split the concatenated text into pieces

            split_texts = re.split(r'\b(TEXT \d+|TEXTS \d+-\d+)\b', concatenated_text)

            '''
            strip whitespace from each piece and filter out empty strings,
            also making sure that each piece starts with "TEXT " or "TEXTS "
            and that it is not empty
            '''

            split_texts = [piece.strip() for piece in split_texts if piece.strip().startswith(('TEXT ', 'TEXTS '))]

            # close the connection

            garg.close()

            # return the formatted texts

            return split_texts
        
    # if the chapter is not found, raise an error

    raise ValueError(f"{canto_chapter} not found in SB.")