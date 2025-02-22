import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
import random

class QuestionGenerator:
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        try:
            nltk.data.find('taggers/averaged_perceptron_tagger')
        except LookupError:
            nltk.download('averaged_perceptron_tagger')
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')

        # Initialize additional attributes
        self.subjects = set()
        self.topics = set()

    def generate_questions(self, text, num_questions):
        """Generate MCQs from the given text"""
        # Split text into sentences
        sentences = sent_tokenize(text)
        
        # Filter out short sentences and select random sentences for question generation
        valid_sentences = [s for s in sentences if len(s.split()) > 10]
        selected_sentences = random.sample(valid_sentences, min(num_questions, len(valid_sentences)))
        
        questions = []
        for sentence in selected_sentences:
            try:
                # Generate question from sentence
                question = self._generate_single_question(sentence)
                if question:
                    # Generate distractors (wrong options)
                    options = self._generate_options(sentence, question['answer'])
                    
                    # Extract subject and topic from the sentence
                    self._extract_subject_topic(sentence)

                    questions.append({
                        'question': question['question'],
                        'options': options,
                        'correct_answer': 0,  # Index of correct answer
                        'context': sentence,
                        'explanation': f"The correct answer is derived from the context: '{sentence}'",
                        'subject': self.subjects,
                        'topic': self.topics
                    })
            except Exception as e:
                print(f"Error generating question for sentence: {str(e)}")
                continue
                
        return questions

    def _extract_subject_topic(self, sentence):
        """Extract subject and topic from the sentence"""
        # Simple heuristic for extracting subjects/topics
        if "mathematics" in sentence.lower():
            self.subjects.add("Mathematics")
            self.topics.add("Algebra")
        elif "science" in sentence.lower():
            self.subjects.add("Science")
            self.topics.add("Physics")
        elif "english" in sentence.lower():
            self.subjects.add("English")
            self.topics.add("Grammar")

    def _generate_single_question(self, sentence):
        """Generate a single question from a sentence"""
        words = word_tokenize(sentence)
        tagged = pos_tag(words)
        
        # Find important words that could be used as answers
        important_words = []
        numbers = []
        
        for word, tag in tagged:
            # Check for numbers (including those written as words)
            try:
                float(word)
                numbers.append(word)
            except ValueError:
                # Check for word-form numbers
                if word.lower() in ['zero', 'one', 'two', 'three', 'four', 'five', 
                                  'six', 'seven', 'eight', 'nine', 'ten']:
                    numbers.append(word)
                # Check for important words
                elif tag.startswith(('NN', 'VB', 'JJ', 'CD')) and len(word) > 3:
                    important_words.append(word)
        
        # Combine numbers and important words, prioritizing numbers
        candidate_answers = numbers + important_words
        
        if not candidate_answers:
            return None
        
        # Select a random answer, preferring numbers if available
        answer = random.choice(numbers) if numbers else random.choice(important_words)
        
        # Create question based on answer type
        try:
            float(answer)
            question = f"What is the numerical value in this context: {sentence.replace(answer, '_____')}"
        except ValueError:
            question = f"What word completes this sentence: {sentence.replace(answer, '_____')}"
        
        return {
            'question': question,
            'answer': answer
        }

    def _generate_options(self, context, correct_answer, num_options=4):
        """Generate multiple choice options including the correct answer"""
        # Check if the correct answer is numeric
        try:
            correct_num = float(correct_answer)
            is_numeric = True
        except ValueError:
            is_numeric = False

        options = [correct_answer]
        
        if is_numeric:
            # Generate numerical options around the correct answer
            base = correct_num
            variations = [
                base * 0.5,  # Half
                base * 1.5,  # One and half
                base * 2,    # Double
                base + 1,    # Plus one
                base - 1,    # Minus one
                base * 0.75, # Three quarters
                base * 1.25  # One and quarter
            ]
            # Select random variations
            distractors = random.sample(variations, min(num_options - 1, len(variations)))
            # Format numbers to match correct_answer precision
            if '.' in str(correct_num):
                decimal_places = len(str(correct_num).split('.')[1])
                distractors = [round(d, decimal_places) for d in distractors]
            else:
                distractors = [int(d) for d in distractors]
            options.extend([str(d) for d in distractors])
        else:
            # For text answers, combine different approaches
            words = word_tokenize(context)
            tagged = pos_tag(words)
            
            # Find words with similar POS tag
            correct_tag = pos_tag([correct_answer])[0][1]
            similar_words = [word for word, tag in tagged 
                           if tag == correct_tag and word != correct_answer 
                           and len(word) > 3]  # Ensure meaningful words
            
            # Add some random words from NLTK's word lists
            if len(similar_words) < num_options - 1:
                all_words = nltk.corpus.words.words()
                random_words = [w for w in random.sample(all_words, num_options * 2)
                              if len(w) > 3 and w.isalpha()]  # Filter meaningful words
                similar_words.extend(random_words)
            
            # Select random distractors
            distractors = random.sample(similar_words, min(num_options - 1, len(similar_words)))
            options.extend(distractors)

        # Ensure we have enough options
        while len(options) < num_options:
            if is_numeric:
                new_val = float(correct_answer) * random.uniform(0.1, 3.0)
                if '.' in str(correct_num):
                    new_val = round(new_val, decimal_places)
                else:
                    new_val = int(new_val)
                options.append(str(new_val))
            else:
                options.append(f"Option {len(options) + 1}")

        # Shuffle options
        random.shuffle(options)
        return options[:num_options]

    def evaluate_performance(self, questions, answers):
        """Evaluate user performance on the quiz"""
        total_questions = len(questions)
        correct_answers = sum(1 for q, a in zip(questions, answers) if q['correct_answer'] == a)
        incorrect_questions = [
            {
                'question': q['question'],
                'your_answer': q['options'][a],
                'correct_answer': q['options'][q['correct_answer']],
                'explanation': q['explanation']
            }
            for q, a in zip(questions, answers)
            if q['correct_answer'] != a
        ]
        
        return {
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'score_percentage': (correct_answers / total_questions) * 100,
            'incorrect_questions': incorrect_questions
        }
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        try:
            nltk.data.find('taggers/averaged_perceptron_tagger')
        except LookupError:
            nltk.download('averaged_perceptron_tagger')
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')

    def generate_questions(self, text, num_questions):
        """Generate MCQs from the given text"""
        # Split text into sentences
        sentences = sent_tokenize(text)
        
        # Filter out short sentences and select random sentences for question generation
        valid_sentences = [s for s in sentences if len(s.split()) > 10]
        selected_sentences = random.sample(valid_sentences, min(num_questions, len(valid_sentences)))
        
        questions = []
        for sentence in selected_sentences:
            try:
                # Generate question from sentence
                question = self._generate_single_question(sentence)
                if question:
                    # Generate distractors (wrong options)
                    options = self._generate_options(sentence, question['answer'])
                    
                    questions.append({
                        'question': question['question'],
                        'options': options,
                        'correct_answer': 0,  # Index of correct answer
                        'context': sentence,
                        'explanation': f"The correct answer is derived from the context: '{sentence}'"
                    })
            except Exception as e:
                print(f"Error generating question for sentence: {str(e)}")
                continue
                
        return questions

    def _generate_single_question(self, sentence):
        """Generate a single question from a sentence"""
        words = word_tokenize(sentence)
        tagged = pos_tag(words)
        
        # Find important words that could be used as answers
        important_words = []
        numbers = []
        
        for word, tag in tagged:
            # Check for numbers (including those written as words)
            try:
                float(word)
                numbers.append(word)
            except ValueError:
                # Check for word-form numbers
                if word.lower() in ['zero', 'one', 'two', 'three', 'four', 'five', 
                                  'six', 'seven', 'eight', 'nine', 'ten']:
                    numbers.append(word)
                # Check for important words
                elif tag.startswith(('NN', 'VB', 'JJ', 'CD')) and len(word) > 3:
                    important_words.append(word)
        
        # Combine numbers and important words, prioritizing numbers
        candidate_answers = numbers + important_words
        
        if not candidate_answers:
            return None
        
        # Select a random answer, preferring numbers if available
        answer = random.choice(numbers) if numbers else random.choice(important_words)
        
        # Create question based on answer type
        try:
            float(answer)
            question = f"What is the numerical value in this context: {sentence.replace(answer, '_____')}"
        except ValueError:
            question = f"What word completes this sentence: {sentence.replace(answer, '_____')}"
        
        return {
            'question': question,
            'answer': answer
        }

    def _generate_options(self, context, correct_answer, num_options=4):
        """Generate multiple choice options including the correct answer"""
        # Check if the correct answer is numeric
        try:
            correct_num = float(correct_answer)
            is_numeric = True
        except ValueError:
            is_numeric = False

        options = [correct_answer]
        
        if is_numeric:
            # Generate numerical options around the correct answer
            base = correct_num
            variations = [
                base * 0.5,  # Half
                base * 1.5,  # One and half
                base * 2,    # Double
                base + 1,    # Plus one
                base - 1,    # Minus one
                base * 0.75, # Three quarters
                base * 1.25  # One and quarter
            ]
            # Select random variations
            distractors = random.sample(variations, min(num_options - 1, len(variations)))
            # Format numbers to match correct_answer precision
            if '.' in str(correct_num):
                decimal_places = len(str(correct_num).split('.')[1])
                distractors = [round(d, decimal_places) for d in distractors]
            else:
                distractors = [int(d) for d in distractors]
            options.extend([str(d) for d in distractors])
        else:
            # For text answers, combine different approaches
            words = word_tokenize(context)
            tagged = pos_tag(words)
            
            # Find words with similar POS tag
            correct_tag = pos_tag([correct_answer])[0][1]
            similar_words = [word for word, tag in tagged 
                           if tag == correct_tag and word != correct_answer 
                           and len(word) > 3]  # Ensure meaningful words
            
            # Add some random words from NLTK's word lists
            if len(similar_words) < num_options - 1:
                all_words = nltk.corpus.words.words()
                random_words = [w for w in random.sample(all_words, num_options * 2)
                              if len(w) > 3 and w.isalpha()]  # Filter meaningful words
                similar_words.extend(random_words)
            
            # Select random distractors
            distractors = random.sample(similar_words, min(num_options - 1, len(similar_words)))
            options.extend(distractors)

        # Ensure we have enough options
        while len(options) < num_options:
            if is_numeric:
                new_val = float(correct_answer) * random.uniform(0.1, 3.0)
                if '.' in str(correct_num):
                    new_val = round(new_val, decimal_places)
                else:
                    new_val = int(new_val)
                options.append(str(new_val))
            else:
                options.append(f"Option {len(options) + 1}")

        # Shuffle options
        random.shuffle(options)
        return options[:num_options]

    def evaluate_performance(self, questions, answers):
        """Evaluate user performance on the quiz"""
        total_questions = len(questions)
        correct_answers = sum(1 for q, a in zip(questions, answers) if q['correct_answer'] == a)
        incorrect_questions = [
            {
                'question': q['question'],
                'your_answer': q['options'][a],
                'correct_answer': q['options'][q['correct_answer']],
                'explanation': q['explanation']
            }
            for q, a in zip(questions, answers)
            if q['correct_answer'] != a
        ]
        
        return {
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'score_percentage': (correct_answers / total_questions) * 100,
            'incorrect_questions': incorrect_questions
        }
