"""
Generates 50 realistic meeting transcripts with complex scenarios for testing.
Each transcript includes multiple speakers, tasks, dates, ambiguous assignments, etc.
"""

import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any


class MeetingScenarioGenerator:
    """Generates realistic meeting scenarios with various complexities."""
    
    # Meeting types with different characteristics
    MEETING_TYPES = [
        "Sprint Planning", "Daily Standup", "Product Review", "Engineering Sync",
        "Marketing Campaign", "Sales Strategy", "Design Review", "Budget Planning",
        "Retrospective", "Client Kickoff", "Security Audit", "Performance Review",
        "Launch Planning", "Architecture Discussion", "User Research", "Crisis Management",
        "Quarterly Planning", "Team Building", "Technical Debt", "API Design",
        "Data Migration", "Compliance Review", "Customer Feedback", "Partnership Discussion",
        "Vendor Selection", "Infrastructure Planning", "Training Session", "Beta Launch",
        "Feature Prioritization", "Bug Triage", "Documentation Review", "Release Planning"
    ]
    
    # Diverse set of names
    NAMES = [
        "Alex", "Emily", "Sarah", "Michael", "David", "Jessica", "James", "Jennifer",
        "Chris", "Amanda", "Daniel", "Lisa", "Matthew", "Rachel", "Kevin", "Laura",
        "Brian", "Michelle", "Ryan", "Nicole", "Andrew", "Stephanie", "Jason", "Rebecca",
        "Justin", "Amy", "Robert", "Melissa", "John", "Angela", "William", "Kimberly",
        "Tom", "Helen", "Mark", "Patricia", "Eric", "Linda", "Steven", "Barbara",
        "Tim", "Susan", "Paul", "Karen", "Jeff", "Nancy", "Scott", "Betty", "Peter", "Sandra"
    ]
    
    # Date expressions (explicit and relative)
    DATE_EXPRESSIONS = [
        "tomorrow", "by end of day", "by EOD", "next Monday", "next Tuesday", 
        "next Wednesday", "next Thursday", "next Friday", "this week", "next week",
        "by Friday", "by the end of this week", "by end of next week",
        "in two weeks", "in three weeks", "by month end", "early next week",
        "middle of next week", "late next week", "first thing Monday morning",
        "ASAP", "as soon as possible", "immediately", "urgent",
        "before the meeting", "after lunch", "by noon tomorrow",
        "within 48 hours", "in the next few days", "sometime this week",
        "no later than Friday", "before next sprint", "by the sprint review",
        "January 15th", "February 1st", "March 20th", "April 10th", "May 5th",
        "on the 15th", "on the 20th", "15th of next month", "20th of this month"
    ]
    
    # Task patterns (explicit, implicit, ambiguous)
    TASK_TEMPLATES = {
        "explicit": [
            "{name}, can you {action}?",
            "{name}, please {action}",
            "{name}, I need you to {action}",
            "{name} will {action}",
            "{name} is going to {action}",
            "Let's have {name} {action}",
            "I'll assign {name} to {action}",
            "{name}, you're responsible for {action}",
        ],
        "implicit": [
            "We need to {action}",
            "Someone should {action}",
            "It would be great if we could {action}",
            "Let's make sure we {action}",
            "Don't forget to {action}",
            "We should probably {action}",
            "I think we need to {action}",
            "Maybe we can {action}",
        ],
        "commitment": [
            "I'll {action}",
            "I can {action}",
            "I'll take care of {action}",
            "Let me {action}",
            "I'll handle {action}",
            "I'll make sure to {action}",
            "I can definitely {action}",
        ],
        "collaborative": [
            "{name1} and {name2}, could you both {action}?",
            "Let's have {name1} and {name2} work together to {action}",
            "{name1}, can you work with {name2} to {action}?",
            "I think {name1} and {name2} should collaborate on {action}",
        ]
    }
    
    # Actions for different meeting types
    ACTIONS = {
        "technical": [
            "review the API documentation",
            "fix the authentication bug",
            "optimize the database queries",
            "update the deployment scripts",
            "write unit tests for the new feature",
            "refactor the legacy code",
            "implement the caching layer",
            "investigate the performance issues",
            "migrate the data to the new schema",
            "set up the CI/CD pipeline",
            "review the security vulnerabilities",
            "update the dependencies",
            "write technical specifications",
            "create the architecture diagram",
            "profile the application performance",
        ],
        "product": [
            "gather user feedback on the new feature",
            "analyze the usage metrics",
            "create wireframes for the dashboard",
            "prioritize the product backlog",
            "schedule user interviews",
            "write user stories for the next sprint",
            "review competitor features",
            "define success metrics",
            "create the product roadmap",
            "update the feature specifications",
        ],
        "marketing": [
            "draft the email campaign",
            "schedule social media posts",
            "prepare the press release",
            "design the landing page",
            "analyze campaign performance",
            "reach out to influencers",
            "create content calendar",
            "update the website copy",
            "prepare marketing materials",
            "coordinate with the PR team",
        ],
        "business": [
            "prepare the quarterly report",
            "schedule a call with the client",
            "review the budget proposal",
            "negotiate the contract terms",
            "send out the meeting invites",
            "follow up with stakeholders",
            "prepare the presentation slides",
            "update the project timeline",
            "document the meeting notes",
            "coordinate with other teams",
        ]
    }
    
    def __init__(self, reference_date: datetime = None):
        """Initialize with a reference date."""
        self.reference_date = reference_date or datetime.now()
        
    def generate_transcript(self, meeting_num: int) -> Dict[str, Any]:
        """Generate a single realistic meeting transcript."""
        meeting_type = self.MEETING_TYPES[meeting_num % len(self.MEETING_TYPES)]
        num_speakers = random.randint(3, 7)
        speakers = random.sample(self.NAMES, num_speakers)
        
        # Determine action categories based on meeting type
        action_categories = self._get_action_categories(meeting_type)
        
        # Generate conversation with tasks
        transcript_segments = []
        ground_truth_tasks = []
        
        # Opening
        transcript_segments.extend(self._generate_opening(speakers, meeting_type))
        
        # Main content with tasks (3-8 tasks per meeting)
        num_tasks = random.randint(3, 8)
        for i in range(num_tasks):
            segments, task = self._generate_task_discussion(
                speakers, action_categories, meeting_num, i
            )
            transcript_segments.extend(segments)
            if task:
                ground_truth_tasks.append(task)
        
        # Closing
        transcript_segments.extend(self._generate_closing(speakers))
        
        # Calculate approximate duration
        total_duration = len(transcript_segments) * 4.5  # ~4.5 seconds per segment
        
        # Create full text
        full_text = " ".join([seg["text"] for seg in transcript_segments])
        
        # Create transcript structure (matching real format)
        transcript = {
            "status": "success",
            "metadata": {
                "file": f"test_meeting_{meeting_num:03d}.mp3",
                "duration": total_duration,
                "model": "whisper-medium",
                "language": "en",
                "processing_time": total_duration * 0.23  # Approximate
            },
            "transcript": transcript_segments,
            "full_text": full_text
        }
        
        return transcript, ground_truth_tasks, meeting_type
    
    def _get_action_categories(self, meeting_type: str) -> List[str]:
        """Determine which action categories to use based on meeting type."""
        type_lower = meeting_type.lower()
        categories = []
        
        if any(x in type_lower for x in ["sprint", "engineering", "technical", "architecture", "api"]):
            categories.append("technical")
        if any(x in type_lower for x in ["product", "review", "feature", "user"]):
            categories.append("product")
        if any(x in type_lower for x in ["marketing", "campaign", "launch"]):
            categories.append("marketing")
        
        categories.append("business")  # Always include business tasks
        return categories
    
    def _generate_opening(self, speakers: List[str], meeting_type: str) -> List[Dict]:
        """Generate meeting opening with realistic conversation."""
        segments = []
        
        # Greeting exchanges
        greetings = [
            "Good morning everyone, let's get started.",
            "Hey everyone, thanks for joining.",
            "Alright team, let's kick this off.",
            "Good morning all, thanks for being here.",
        ]
        
        responses = ["Morning!", "Hey!", "Hello!", "Hi there!", "Good morning!"]
        
        # Leader opens
        segments.append({
            "text": random.choice(greetings),
            "speaker": f"Speaker_{speakers[0]}"
        })
        
        # Others respond
        for i in range(1, min(len(speakers), 3)):
            segments.append({
                "text": random.choice(responses),
                "speaker": f"Speaker_{speakers[i]}"
            })
        
        # Meeting context
        contexts = [
            f"Alright, today's focus is our {meeting_type}.",
            f"So, this is our {meeting_type} session.",
            f"Let's dive into today's {meeting_type}.",
            f"Today we're covering the {meeting_type}.",
        ]
        
        segments.append({
            "text": random.choice(contexts),
            "speaker": f"Speaker_{speakers[0]}"
        })
        
        return segments
    
    def _generate_closing(self, speakers: List[str]) -> List[Dict]:
        """Generate meeting closing with realistic goodbyes."""
        segments = []
        
        # Check for blockers
        segments.append({
            "text": "Is there anything blocking anyone from starting?",
            "speaker": f"Speaker_{speakers[0]}"
        })
        
        # Responses
        no_blocker_responses = [
            "Not from my side.",
            "All good here.",
            "No blockers.",
            "We're good to go.",
            "Nothing blocking me.",
        ]
        
        for i in range(1, min(len(speakers), 3)):
            segments.append({
                "text": random.choice(no_blocker_responses),
                "speaker": f"Speaker_{speakers[i]}"
            })
        
        # Wrap up
        closings = [
            "Excellent. Thanks everyone, let's stay aligned on this.",
            "Great, thanks all. Let's keep each other posted on progress.",
            "Perfect. Thanks everyone, let's make this happen.",
            "Sounds good. Thanks team, looking forward to seeing the results.",
        ]
        
        segments.append({
            "text": random.choice(closings),
            "speaker": f"Speaker_{speakers[0]}"
        })
        
        # Goodbyes
        goodbyes = ["Thanks!", "Will do!", "Sounds good!", "Thanks, talk soon!", "Bye all!", "See you!"]
        
        for i in range(1, min(len(speakers), 3)):
            segments.append({
                "text": random.choice(goodbyes),
                "speaker": f"Speaker_{speakers[i]}"
            })
        
        return segments
    
    def _generate_task_discussion(
        self, 
        speakers: List[str], 
        action_categories: List[str],
        meeting_num: int,
        task_num: int
    ) -> tuple:
        """Generate a realistic discussion segment with a task assignment."""
        segments = []
        
        # Choose assignment pattern
        pattern_type = random.choice(["explicit", "implicit", "commitment", "collaborative"])
        
        # Choose action
        category = random.choice(action_categories)
        action = random.choice(self.ACTIONS[category])
        
        # Choose assignee(s)
        if pattern_type == "collaborative":
            assignees = random.sample(speakers[1:], min(2, len(speakers)-1))
            expected_assignees = assignees
        elif pattern_type == "commitment":
            assignee = random.choice(speakers[1:])
            expected_assignees = [assignee]
        elif pattern_type == "implicit":
            expected_assignees = []
        else:  # explicit
            assignee = random.choice(speakers[1:])
            expected_assignees = [assignee]
        
        # Add deadline
        has_deadline = random.random() > 0.3
        deadline_expr = random.choice(self.DATE_EXPRESSIONS) if has_deadline else None
        
        # Build natural conversation
        # 1. Topic introduction
        intros = [
            f"Let's talk about {category} for a moment.",
            f"Next item is {category}.",
            f"Moving on to {category}.",
            f"On the {category} side,",
        ]
        segments.append({
            "text": random.choice(intros),
            "speaker": f"Speaker_{speakers[0]}"
        })
        
        # 2. Task assignment with context
        if pattern_type == "explicit":
            segments.append({
                "text": f"{expected_assignees[0]}, I'd like you to {action}.",
                "speaker": f"Speaker_{speakers[0]}"
            })
            if has_deadline:
                segments.append({
                    "text": f"Please have this ready by {deadline_expr}.",
                    "speaker": f"Speaker_{speakers[0]}"
                })
            # Response
            acknowledgments = ["Sure, happy to.", "Got it.", "No problem.", "Will do.", "Understood."]
            segments.append({
                "text": random.choice(acknowledgments),
                "speaker": f"Speaker_{expected_assignees[0]}"
            })
            
        elif pattern_type == "collaborative":
            segments.append({
                "text": f"{expected_assignees[0]} and {expected_assignees[1]}, could you both work together to {action}?",
                "speaker": f"Speaker_{speakers[0]}"
            })
            if has_deadline:
                segments.append({
                    "text": f"Target completion is {deadline_expr}.",
                    "speaker": f"Speaker_{speakers[0]}"
                })
            # Responses from both
            segments.append({
                "text": "Yes, we can handle that.",
                "speaker": f"Speaker_{expected_assignees[0]}"
            })
            segments.append({
                "text": "Sounds good to me.",
                "speaker": f"Speaker_{expected_assignees[1]}"
            })
            
        elif pattern_type == "commitment":
            # Someone volunteers
            segments.append({
                "text": f"We need someone to {action}.",
                "speaker": f"Speaker_{speakers[0]}"
            })
            segments.append({
                "text": f"I'll handle that{' ' + deadline_expr if has_deadline else ''}.",
                "speaker": f"Speaker_{expected_assignees[0]}"
            })
            segments.append({
                "text": "Great, thanks for taking that on.",
                "speaker": f"Speaker_{speakers[0]}"
            })
            
        else:  # implicit
            segments.append({
                "text": f"We need to {action}{' by ' + deadline_expr if has_deadline else ''}.",
                "speaker": f"Speaker_{speakers[0]}"
            })
            # Maybe someone responds
            if random.random() > 0.5:
                segments.append({
                    "text": "Agreed, that's important.",
                    "speaker": f"Speaker_{speakers[1]}"
                })
        
        # Ground truth task
        task = {
            "description": action,
            "assignees": expected_assignees if expected_assignees else [],
            "deadline": deadline_expr if has_deadline else None,
            "pattern_type": pattern_type,
            "category": category,
            "has_explicit_assignee": pattern_type in ["explicit", "commitment", "collaborative"],
            "has_deadline": has_deadline
        }
        
        return segments, task
    
    def generate_all_transcripts(self, output_dir: Path, num_transcripts: int = 50):
        """Generate all test transcripts and ground truth data."""
        output_dir.mkdir(parents=True, exist_ok=True)
        transcripts_dir = output_dir / "transcripts"
        ground_truth_dir = output_dir / "ground_truth"
        transcripts_dir.mkdir(exist_ok=True)
        ground_truth_dir.mkdir(exist_ok=True)
        
        all_stats = {
            "total_transcripts": num_transcripts,
            "total_tasks": 0,
            "tasks_with_assignees": 0,
            "tasks_with_deadlines": 0,
            "pattern_types": {},
            "categories": {},
            "generation_date": datetime.now().isoformat()
        }
        
        print(f"🎬 Generating {num_transcripts} realistic meeting transcripts...")
        
        for i in range(num_transcripts):
            transcript, ground_truth, meeting_type = self.generate_transcript(i)
            
            # Save transcript
            transcript_file = transcripts_dir / f"meeting_{i:03d}.json"
            with open(transcript_file, 'w', encoding='utf-8') as f:
                json.dump(transcript, f, indent=2, ensure_ascii=False)
            
            # Save ground truth
            ground_truth_file = ground_truth_dir / f"meeting_{i:03d}_ground_truth.json"
            with open(ground_truth_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "meeting_file": f"meeting_{i:03d}.json",
                    "meeting_type": meeting_type,
                    "tasks": ground_truth
                }, f, indent=2, ensure_ascii=False)
            
            # Update stats
            all_stats["total_tasks"] += len(ground_truth)
            for task in ground_truth:
                if task["assignees"]:
                    all_stats["tasks_with_assignees"] += 1
                if task["has_deadline"]:
                    all_stats["tasks_with_deadlines"] += 1
                
                pattern = task["pattern_type"]
                all_stats["pattern_types"][pattern] = all_stats["pattern_types"].get(pattern, 0) + 1
                
                category = task["category"]
                all_stats["categories"][category] = all_stats["categories"].get(category, 0) + 1
            
            if (i + 1) % 10 == 0:
                print(f"  ✓ Generated {i + 1}/{num_transcripts} transcripts")
        
        # Save summary
        summary_file = output_dir / "dataset_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(all_stats, f, indent=2)
        
        print(f"\n✅ Generated {num_transcripts} transcripts successfully!")
        print(f"📊 Statistics:")
        print(f"   Total tasks: {all_stats['total_tasks']}")
        print(f"   Tasks with assignees: {all_stats['tasks_with_assignees']}")
        print(f"   Tasks with deadlines: {all_stats['tasks_with_deadlines']}")
        print(f"   Pattern distribution: {all_stats['pattern_types']}")
        print(f"   Category distribution: {all_stats['categories']}")
        print(f"\n📁 Output directory: {output_dir}")


if __name__ == "__main__":
    output_dir = Path(__file__).parent / "test_data_50"
    generator = MeetingScenarioGenerator()
    generator.generate_all_transcripts(output_dir, num_transcripts=50)
