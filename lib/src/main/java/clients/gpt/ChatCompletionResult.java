package clients.gpt;

import java.util.List;

public class ChatCompletionResult {

	    /**
	     * Unique id assigned to this chat completion.
	     */
	    String id;

	    /**
	     * The type of object returned, should be "chat.completion"
	     */
	    String object;

	    /**
	     * The creation time in epoch seconds.
	     */
	    long created;
	    
	    /**
	     * The GPT model used.
	     */
	    String model;

	    /**
	     * A list of all generated completions.
	     */
	    List<CompletionChoice> choices;

	    /**
	     * The API usage for this request.
	     */
	    Usage usage;


}
