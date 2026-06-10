package com.smartnotes.java_backend;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/notes")
public class NoteController {

    @Autowired
    private NoteRepository noteRepository;

    @Autowired
    private S3Service s3Service; // Inject our new S3 Service

    @PostMapping
    public Note createNote(@RequestBody Note note) {
        // Step 1: Save metadata & content to AWS RDS PostgreSQL
        Note savedNote = noteRepository.save(note);

        // Step 2: Use the auto-generated database ID to make a unique filename for S3
        String s3FileName = "note_" + savedNote.getId() + ".txt";

        // Step 3: Stream the raw text to your S3 bucket backup folder
        try {
            s3Service.uploadTextFile(s3FileName, savedNote.getContent());
            System.out.println("Successfully backed up note content to S3: " + s3FileName);
        } catch (Exception e) {
            System.err.println("Database saved, but failed to upload to S3: " + e.getMessage());
        }

        return savedNote;
    }

    @GetMapping
    public List<Note> getAllNotes() {
        return noteRepository.findAll();
    }
}